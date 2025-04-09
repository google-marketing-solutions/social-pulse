# Social Pulse - Common

This sub-project contains the common shared library of tools and messages used
by other parts of the Social Pulse solution.

## Set up
If you downloaded the Social Puse solution for the first time, you'll need
to run the following commands to get the latest common code ready to be used
by the micro-services.

1. Enter into the shared library root directory.  Assuming you checked out the
   repo into ```~/myprojects/social_pulse```
  ```
  cd ~/myprojects/social_pulse/services/shared_lib
  ```

2. Install all the dependecies
  ```
  pip install -r requirements.txt
  ```

3. Run the protobuf compiler to generate the Python messages
  ```
  protoc \
    --proto_path=$(pwd)/src/socialpulse_common/messages/proto \
    --python_out=$(pwd)/src/socialpulse_common/messages \
    $(pwd)/src/socialpulse_common/messages/proto/*.proto
  ```

4. Build the distribution
  ```
  python -m build
  ```

5. Re-install the packaged commons distribution
  ```
  cd ../analysis_service
  pip install -r requirements.txt
  ```
