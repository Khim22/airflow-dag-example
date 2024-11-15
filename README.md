# airflow-dag-example


## Handling conflicting/complex Python dependencies

-> https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#best-practices-handling-conflicting-complex-python-dependencies
Airflow has many Python dependencies and sometimes the Airflow dependencies are conflicting with dependencies that your task code expects. Since - by default - Airflow environment is just a single set of Python dependencies and single Python environment, often there might also be cases that some of your tasks require different dependencies than other tasks and the dependencies basically conflict between those tasks.

If you are using pre-defined Airflow Operators to talk to external services, there is not much choice, but usually those operators will have dependencies that are not conflicting with basic Airflow dependencies. Airflow uses constraints mechanism which means that you have a “fixed” set of dependencies that the community guarantees that Airflow can be installed with (including all community providers) without triggering conflicts. However, you can upgrade the providers independently and their constraints do not limit you, so the chance of a conflicting dependency is lower (you still have to test those dependencies). Therefore, when you are using pre-defined operators, chance is that you will have little, to no problems with conflicting dependencies.

However, when you are approaching Airflow in a more “modern way”, where you use TaskFlow Api and most of your operators are written using custom python code, or when you want to write your own Custom Operator, you might get to the point where the dependencies required by the custom code of yours are conflicting with those of Airflow, or even that dependencies of several of your Custom Operators introduce conflicts between themselves.

There are a number of strategies that can be employed to mitigate the problem. And while dealing with dependency conflict in custom operators is difficult, it’s actually quite a bit easier when it comes to using airflow.operators.python.PythonVirtualenvOperator or airflow.operators.python.ExternalPythonOperator - either directly using classic “operator” approach or by using tasks decorated with @task.virtualenv or @task.external_python decorators if you use TaskFlow.

Let’s start from the strategies that are easiest to implement (having some limits and overhead), and we will gradually go through those strategies that requires some changes in your Airflow deployment.

Using PythonVirtualenvOperator
This is simplest to use and most limited strategy. The PythonVirtualenvOperator allows you to dynamically create a virtualenv that your Python callable function will execute in. In the modern TaskFlow approach described in Working with TaskFlow. this also can be done with decorating your callable with @task.virtualenv decorator (recommended way of using the operator). Each airflow.operators.python.PythonVirtualenvOperator task can have its own independent Python virtualenv (dynamically created every time the task is run) and can specify fine-grained set of requirements that need to be installed for that task to execute.

The operator takes care of:

creating the virtualenv based on your environment

serializing your Python callable and passing it to execution by the virtualenv Python interpreter

executing it and retrieving the result of the callable and pushing it via xcom if specified

The benefits of the operator are:

There is no need to prepare the venv upfront. It will be dynamically created before task is run, and removed after it is finished, so there is nothing special (except having virtualenv package in your airflow dependencies) to make use of multiple virtual environments

You can run tasks with different sets of dependencies on the same workers - thus Memory resources are reused (though see below about the CPU overhead involved in creating the venvs).

In bigger installations, DAG Authors do not need to ask anyone to create the venvs for you. As a DAG Author, you only have to have virtualenv dependency installed and you can specify and modify the environments as you see fit.

No changes in deployment requirements - whether you use Local virtualenv, or Docker, or Kubernetes, the tasks will work without adding anything to your deployment.

No need to learn more about containers, Kubernetes as a DAG Author. Only knowledge of Python requirements is required to author DAGs this way.

There are certain limitations and overhead introduced by this operator:

Your python callable has to be serializable. There are a number of python objects that are not serializable using standard pickle library. You can mitigate some of those limitations by using dill library but even that library does not solve all the serialization limitations.

All dependencies that are not available in the Airflow environment must be locally imported in the callable you use and the top-level Python code of your DAG should not import/use those libraries.

The virtual environments are run in the same operating system, so they cannot have conflicting system-level dependencies (apt or yum installable packages). Only Python dependencies can be independently installed in those environments.

The operator adds a CPU, networking and elapsed time overhead for running each task - Airflow has to re-create the virtualenv from scratch for each task

The workers need to have access to PyPI or private repositories to install dependencies

The dynamic creation of virtualenv is prone to transient failures (for example when your repo is not available or when there is a networking issue with reaching the repository)

It’s easy to fall into a “too” dynamic environment - since the dependencies you install might get upgraded and their transitive dependencies might get independent upgrades you might end up with the situation where your task will stop working because someone released a new version of a dependency or you might fall a victim of “supply chain” attack where new version of a dependency might become malicious

The tasks are only isolated from each other via running in different environments. This makes it possible that running tasks will still interfere with each other - for example subsequent tasks executed on the same worker might be affected by previous tasks creating/modifying files etc.

You can see detailed examples of using airflow.operators.python.PythonVirtualenvOperator in Taskflow Virtualenv example

Using ExternalPythonOperator
New in version 2.4.

A bit more involved but with significantly less overhead, security, stability problems is to use the airflow.operators.python.ExternalPythonOperator`. In the modern TaskFlow approach described in Working with TaskFlow. this also can be done with decorating your callable with @task.external_python decorator (recommended way of using the operator). It requires, however, that you have a pre-existing, immutable Python environment, that is prepared upfront. Unlike in airflow.operators.python.PythonVirtualenvOperator you cannot add new dependencies to such pre-existing environment. All dependencies you need should be added upfront in your environment and available in all the workers in case your Airflow runs in a distributed environment.

This way you avoid the overhead and problems of re-creating the virtual environment but they have to be prepared and deployed together with Airflow installation. Usually people who manage Airflow installation need to be involved, and in bigger installations those are usually different people than DAG Authors (DevOps/System Admins).

Those virtual environments can be prepared in various ways - if you use LocalExecutor they just need to be installed at the machine where scheduler is run, if you are using distributed Celery virtualenv installations, there should be a pipeline that installs those virtual environments across multiple machines, finally if you are using Docker Image (for example via Kubernetes), the virtualenv creation should be added to the pipeline of your custom image building.

The benefits of the operator are:

No setup overhead when running the task. The virtualenv is ready when you start running a task.

You can run tasks with different sets of dependencies on the same workers - thus all resources are reused.

There is no need to have access by workers to PyPI or private repositories. Less chance for transient errors resulting from networking.

The dependencies can be pre-vetted by the admins and your security team, no unexpected, new code will be added dynamically. This is good for both, security and stability.

Limited impact on your deployment - you do not need to switch to Docker containers or Kubernetes to make a good use of the operator.

No need to learn more about containers, Kubernetes as a DAG Author. Only knowledge of Python, requirements is required to author DAGs this way.

The drawbacks:

Your environment needs to have the virtual environments prepared upfront. This usually means that you cannot change it on the fly, adding new or changing requirements require at least an Airflow re-deployment and iteration time when you work on new versions might be longer.

Your python callable has to be serializable. There are a number of python objects that are not serializable using standard pickle library. You can mitigate some of those limitations by using dill library but even that library does not solve all the serialization limitations.

All dependencies that are not available in Airflow environment must be locally imported in the callable you use and the top-level Python code of your DAG should not import/use those libraries.

The virtual environments are run in the same operating system, so they cannot have conflicting system-level dependencies (apt or yum installable packages). Only Python dependencies can be independently installed in those environments

The tasks are only isolated from each other via running in different environments. This makes it possible that running tasks will still interfere with each other - for example subsequent tasks executed on the same worker might be affected by previous tasks creating/modifying files et.c

You can think about the PythonVirtualenvOperator and ExternalPythonOperator as counterparts - that make it smoother to move from development phase to production phase. As a DAG author you’d normally iterate with dependencies and develop your DAG using PythonVirtualenvOperator (thus decorating your tasks with @task.virtualenv decorators) while after the iteration and changes you would likely want to change it for production to switch to the ExternalPythonOperator (and @task.external_python) after your DevOps/System Admin teams deploy your new dependencies in pre-existing virtualenv in production. The nice thing about this is that you can switch the decorator back at any time and continue developing it “dynamically” with PythonVirtualenvOperator.

You can see detailed examples of using airflow.operators.python.ExternalPythonOperator in Taskflow External Python example

Using DockerOperator or Kubernetes Pod Operator
Another strategy is to use the airflow.providers.docker.operators.docker.DockerOperator airflow.providers.cncf.kubernetes.operators.pod.KubernetesPodOperator Those require that Airflow has access to a Docker engine or Kubernetes cluster.

Similarly as in case of Python operators, the taskflow decorators are handy for you if you would like to use those operators to execute your callable Python code.

However, it is far more involved - you need to understand how Docker/Kubernetes Pods work if you want to use this approach, but the tasks are fully isolated from each other and you are not even limited to running Python code. You can write your tasks in any Programming language you want. Also your dependencies are fully independent from Airflow ones (including the system level dependencies) so if your task require a very different environment, this is the way to go.

New in version 2.2.

As of version 2.2 of Airflow you can use @task.docker decorator to run your functions with DockerOperator.

New in version 2.4.

As of version 2.2 of Airflow you can use @task.kubernetes decorator to run your functions with KubernetesPodOperator.

The benefits of using those operators are:

You can run tasks with different sets of both Python and system level dependencies, or even tasks written in completely different language or even different processor architecture (x86 vs. arm).

The environment used to run the tasks enjoys the optimizations and immutability of containers, where a similar set of dependencies can effectively reuse a number of cached layers of the image, so the environment is optimized for the case where you have multiple similar, but different environments.

The dependencies can be pre-vetted by the admins and your security team, no unexpected, new code will be added dynamically. This is good for both, security and stability.

Complete isolation between tasks. They cannot influence one another in other ways than using standard Airflow XCom mechanisms.

The drawbacks:

There is an overhead to start the tasks. Usually not as big as when creating virtual environments dynamically, but still significant (especially for the KubernetesPodOperator).

In case of TaskFlow decorators, the whole method to call needs to be serialized and sent over to the Docker Container or Kubernetes Pod, and there are system-level limitations on how big the method can be. Serializing, sending, and finally deserializing the method on remote end also adds an overhead.

There is a resources overhead coming from multiple processes needed. Running tasks in case of those two operators requires at least two processes - one process (running in Docker Container or Kubernetes Pod) executing the task, and a supervising process in the Airflow worker that submits the job to Docker/Kubernetes and monitors the execution.

Your environment needs to have the container images ready upfront. This usually means that you cannot change them on the fly. Adding system dependencies, modifying or changing Python requirements requires an image rebuilding and publishing (usually in your private registry). Iteration time when you work on new dependencies are usually longer and require the developer who is iterating to build and use their own images during iterations if they change dependencies. An appropriate deployment pipeline here is essential to be able to reliably maintain your deployment.

Your python callable has to be serializable if you want to run it via decorators, also in this case all dependencies that are not available in Airflow environment must be locally imported in the callable you use and the top-level Python code of your DAG should not import/use those libraries.

You need to understand more details about how Docker Containers or Kubernetes work. The abstraction provided by those two are “leaky”, so you need to understand a bit more about resources, networking, containers etc. in order to author a DAG that uses those operators.

You can see detailed examples of using airflow.operators.providers.Docker in Taskflow Docker example and airflow.providers.cncf.kubernetes.operators.pod.KubernetesPodOperator Taskflow Kubernetes example