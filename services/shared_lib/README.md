# Social Pulse - Common

This sub-project contains the common shared library of tools and messages used
by other parts of the Social Pulse solution.

## Local Development Environment

This library is designed to be developed locally and deployed as a Python
package (wheel) to be consumed by the Analysis and Reporting services.

### Environment Setup

First, create a virtual environment for the shared library and install the
development requirements.

```bash
# Create and activate virtual environment
python3 -m venv .venv --prompt "social_pulse_common"
source .venv/bin/activate

# Install development dependencies
pip install -r base-tooling-requirements.txt

# Install the library dependencies
pip install -r requirements.txt
```

## Deploying Locally

When you make changes to `socialpulse-common`, you need to build the package
and make it available to the other services. We use a local PyPI server workflow
for this.

Run the local deployment script to:
1.  Build the `socialpulse-common` wheel.
2.  Start a local package server (on port 3322).
3.  Update `requirements.txt` in `analysis_service` and `report_service` with
    the new package hash.

```bash
./deploy_to_local.sh
```

**Note:** The script will verify if the local PyPI server is already running and
start it if necessary.

### Updating Dependent Services

Once you have deployed the changes locally, you need to reinstall the
dependencies in the consuming services (Analysis Service or Report Service).

Navigate to the service directory and install the updated requirements using the
local package index:

```bash
# Example for Analysis Service
cd ../analysis_service
source .venv/bin/activate  # Ensure you are in the service's venv

pip install -r requirements.txt \
    --extra-index-url http://localhost:3322/simple \
    --trusted-host localhost
```

## Dependency Management

This project uses `pip-compile` to manage the `requirements.txt` file based on
`requirements.in`. Hash checking is enforced for security.

If you need to add or update a dependency:

1.  Edit `requirements.in`.
2.  Compile the new requirements:
    ```bash
    pip-compile \
       --generate-hashes \
       --no-emit-index-url \
       requirements.in
    ```

## Cloud Deployment

For production deployment, the library is published to Google Cloud Artifact
Registry.
