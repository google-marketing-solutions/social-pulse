# Social Pulse - Common

This sub-project contains the common shared library of tools and messages used
by other parts of the Social Pulse solution.


## Deployment Workflow

Whenever you make changes to this `socialpulse-common` library, you must rebuild
the package and update the dependent services (`analysis_service` and
`report_service`) before building their Docker images (for production
deployment) or running the services locally (for local development).

A script has been provided to automate this entire process.

### Making changes to the project dependecies

This project uses `pip-compile` to manage the `requirements.txt` file, based on
the dependencies listed in the `requirements.in` file.  In addition, when
compiling the `requirements.txt` file, hashes are included for additional
security.

If you add a depency, make sure to add the `generate-hashes` flag to the
compile call:

```
pip-compile \
   --generate-hashes \
   --find-links=../shared_lib/dist \
   --no-emit-index-url \
   requirements.in
```
### Running the deployment script

1.  Navigate to the shared library directory:
    ```bash
    cd /path/to/your/project/social_pulse/services/shared_lib
    ```

2.  Make your changes (ie, add a new field to one of the common data classes).

3.  Run the deployment script:
    ```bash
    ./deploy_to_services.sh
    ```

This script handles building the `socialpulse-common` wheel, calculating its new
SHA256 hash, and patching the `requirements.txt` files in all dependent
services.

After running the script, you can proceed to run the deployment scripts or
start up your local web services.
