# Social Pulse

## License and Copyright Notice
> Copyright 2025 Google LLC
>
> Licensed under the Apache License, Version 2.0 (the "License");
> you may not use this file except in compliance with the License.
> You may obtain a copy of the License at
>
>   https://www.apache.org/licenses/LICENSE-2.0
>
> Unless required by applicable law or agreed to in writing, software
> distributed under the License is distributed on an "AS IS" BASIS,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the License for the specific language governing permissions and
> limitations under the License.

## Disclaimer

> This project is provided "as is" and without warranty of any kind, express or
> implied, including but not limited to the warranties of merchantability,
> fitness for a particular purpose and non-infringement. In no event shall the
> authors or copyright holders be liable for any claim, damages or other
> liability, whether in an action of contract, tort or otherwise, arising from,
> out of or in connection with the software or the use or other dealings in the
> software.
>
> Please use this software at your own risk. The author(s) are not responsible
> for any legal implications or consequences resulting from the use or misuse of
> this software.

## Problem Statement

Many advertisers are well known world wide, where large groups of people express
strong opinions - both good and bad - about their products through social
content. Hence, many advertisers are looking to analyze social media content,
to find the following insights:

* Gauge this user sentiment, to see how it might be affecting their sales.
* Gauge what new features their customers are most interested in seeing added
to their products
* Monitor their respective industry, to help find emerging trends and emerging
competitors.

## Solution Description

This solution creates a platform by which advertisers can mine various social
media content (ie, Youtube videos and comments) to extract both 1) sentiment
scores on each piece of social media content, and 2) a relevancy score on how
much the content relates to the topic being analyzed.

The flow of the solution is as follows:

1. The analyzer identifies a topic (ie, "Foo feature for Bar product"), start
and end date to analyze, what social media content they want to analyze (see
details below), and what output they want (see details below).

2. When the solution runs, it will use publicly avaiable APIs to search for
content related to the topic, within the analysis start and end dates, and
from the specified social media content.

3. The solution will then leverage Google Cloud Platform's (GCP) Vertex AI
batch prediction capabilities to leverage Gemini to analyze all of the found
content.

4. Sentiment data is then written to a BigQuery table, where it can be queried
and analyzed.

## Getting Started for Local Development

1. Choose or create a Google Cloud Platform (GCP) project to use to generate
your sentiment analysis reports.  Make sure it has the following:
  a. It's associated with a billing account
  b. It has the YouTube Data API enabled
  c. It has the Vertex AI API enabled
  d. It has the BigQuery API enabled.

2. If you are running the sentiment analysis code on a Linus/Unix system,
   make sure to authenticate yourself to access the Google Could resources
   using the `gcloud auth init` command.

3. Setup a PostgresDB server for storing reporting configuration data.

3. Open up the [Shared Services Library README](./services/shared_lib/README.md)
file and follow the instructions there to set up the common library code used
by the Analysis Service.

4. Open up the [Analysis Service README](./services/analysis_service/README.md)
file and follow the instructions there to get the command line set up.

## FAQ

*Q.  What social media content is currently supported?* \
A. Currently only Youtube video and comments are supported, but we are working
on bringing other content types to the solution.

*Q.  What output formats are currently supported?* \
A.  Currently, only sentiment scores are supported, but we are working on
bringing other output formats to the solution, including justifications (3
quotes from each content that explains why the content is positive or negative).
