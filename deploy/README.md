# Deploying and Running CDP Pipelines

This document details how to deploy and maintain a CDP instance for a new city or for your own personal use. Many of the
examples used during these guide will be exact use cases and problems found during the launch of CDP-Seattle. Your own
instance of CDP for you own city may have it's own issues but generally this document should be all encompassing, and,
if you run into issues during deploying or maintaining your server please feel free to submit a pull request to add to
this document with more notes and information. If you want to deploy an exact replica to CDP-Seattle, jump to the
[configuration and setup](#configuration-and-setup) section.

### Index
1. [Background](#background)
2. [Module Choices](#module-choices)
3. [Back-end Hosting](#back-end-hosting)
4. [Configuration and Setup](#configuration-and-setup)
    * [Local Development Setup](#local-development-setup)
    * [Production Server Setup](#production-server-setup)
5. [Running Pipelines](#running-pipelines)

## Background
It is generally a good practice to have a staging and a production instance of any system that will be mass producing
data so please do that. It is also a primary goal to keep costs of running a CDP instance as low as possible while
still producing high quality data. Quick math says that running a CDP instance should cost anywhere between
$50 - $100 / month. This includes all server, database, transcription, and storage costs but this will vary depending
on which back-end hosting provider you choose and how much traffic your system receives.

There are currently two pipelines you will want to run, the event gathering pipeline (`EventGatherPipeline`) and the
event indexing pipeline (`EventIndexPipeline`). The core of the system is very much the `EventGatherPipeline` as it is
what actually gathers the data from your city, produces a transcript, and standardizes all the retrieved and generated
data into the CDP database and storage formats. The `EventIndexPipeline` is the first of many downstream processing
pipelines. It indexes the transcripts in relation to events to allow for fast plain text search of events. Technically,
this is not a required pipeline to run but plain text search is a leg up on a lot of civic systems and generally a nice
tool.

Each of these pipelines runs in their own process on their own schedule (as determined by you). We will get more into
this in the [configuration and setup](#configuration-and-setup) section but note that because each pipeline runs on it's
own process and requests multiple threads and in some cases spawns additional processes, it may be best to either have
a medium sized host for many of these pipelines to run from, or many smaller hosts that each run a single pipeline.

## Module Choices
As discussed in the [system design](../docs/system_design) document, each pipeline is highly modular. Each pipeline
must have all components but it is designed to be plug-and-play with the different modules. Many module choices will
likely come down to which back-end server host / provider / platform you will use while others modules will likely be
standard across all CDP instances. An example of a module that is likely going to be used across all CDP instances, is
the `FFmpegAudioSplitter` as it is generally the fastest and easiest to use programmable audio splitting interface. The
modules that will be dependent on your back-end server / host / provider / platform would be any `Database` or
`FileStore` as these commonly go together.

Just keep these module choices in mind when deciding which back-end host to use; "If I use this back-end server
provider, are there already made and tested modules that work with this provider or will I have to write my own?".

## Back-end Hosting
This is going to be the biggest choice in deploying a CDP instance. For the easiest integration between all modules, it
is recommended to use Google Cloud Platform. This is because it has a database and file store that live together
(Cloud Firestore), an if your audio files live in a Google Cloud Storage bucket, you can use the already written
`GoogleCloudSRModel` because it requires a `gc://` uri header to work properly (aka: multi-hour-long audio files in a
single transcription request call). All this together means you will have only two credential files, one for a staging
deployment of the entire system and one for the production deployment of the entire system.

Other providers like AWS or Microsoft Azure would require splitting resources across multiple systems. For example, file
storage in AWS S3, database storage in AWS Redshift, but transcription for a different provider, Google Cloud, IBM
Watson, etc. This shouldn't turn you away from these other services as they each have their benefits, but note that the
following [configuration and setup](#configuration-and-setup) section uses Google Cloud as it's entire back-end server
host / provider / platform.

## Configuration and Setup
This section will be broken into a [local development setup](#local-development-setup) section and a
[production server setup](#production-server-setup) section. Local development will point at a staging instance and
production server with point at a production instance.

**Note:** One more notice that these instructions are for an exact copy of CDP-Seattle which uses entirely Google Cloud
products and services.

**Note:** Any terminal commands in the following section assumes you are using a bash terminal.

### Local Development Setup
First let's clone the project:

```bash
git clone https://github.com/CouncilDataProject/cdptools.git
cd cdptools/
```

Let's also preemptively create a credentials folder:

```bash
mkdir credentials
```

**Keep this terminal open for later.**

1. Create a Firebase project by going to [Firebase console](https://console.firebase.google.com/) and clicking the
"Create a project" button.
2. Give the project a name. Because this is a staging deployment, it is recommended to prepend `stg-` to the name for
easy recognition of which deployment you are working with later on. Your staging project's name should look something
like: `stg-cdp-seattle`.
3. Agree with the terms of use and click "Create project".
4. Once the project is done setting up, click "Continue" and you should now have a card available on the same page with
your project name. Click on the card with your project name.
5. You are now at your database and file store console! Time to setup the database. In the upper left of the page, click
on "Develop" to reveal various development tools and options.
6. In the "Develop" section that was just opened, click on "Database".
7. In the upper center of the screen, click on "Create database".
8. Optional: If you want your database and file store to be open access, it doesn't matter if you selected "Start in
locked mode" or "Start in test mode", we will change this soon so simply click "Next". If you want the data to be a
private copy for your own personal use (although we discourage this), it is recommended to make sure "Start in locked
mode" and then click "Next".
9. Optional: If you want a server hosting your database and file store to be specifically in your region, (i.e. North
America west coast, east coast, central), choose which server location you want from the "Cloud Firestore location"
dropdown. By default, server location is set to us-central.
10. Click done to create the database and wait for all the setup and provisioning to finish.
11. Optional: You are now on the data page, before we do anything else, if in step 8 you moved on but you do want to
allow your database and file store to be open access, in the upper left, click "Rules". In the text box on the right
side, copy and paste the following lines of code:

```
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read: if true;
    }
  }
}
```
Click "Publish" to have your database be open access.

12. In the "Develop" section in the upper left again, click on "Storage".
13. Click "Get Started" and follow the prompts. Click "Next". Click "Done".
14. Optional: You are now on the files page, if you want your files to be open access, in the upper left, click "Rules".
In the text box on the right side, copy and paste the following lines of code:

```
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read: if true;
    }
  }
}
```
Click "Publish" to have your file store be open access.

15. You have now setup the database and file store for your CDP instance, time to setup the Google Speech to Text
and add billing to your account. Go to the [Google cloud console](https://console.cloud.google.com/).
16. In the upper left, click on the "Select a project" dropdown. After a brief second, all projects linked to your
Google account should appear. Click on the project that you just created (it will have the same project name that you
entered when you were working with Firebase console).
17. On the left side of the page, hover over "APIs & Services" and then click "Dashboard".
18. At the top of the page, click "+ ENABLE APIS AND SERVICES".
19. In the search bar, type "Cloud Speech-to-Text API", when the results appear, click on the "Cloud Speech-to-Text API"
card.
20. Click "ENABLE". Follow the prompt and click on "ENABLE BILLING". Follow the prompt and click "CREATE BILLING
ACCOUNT".
21. Agree to the terms and click "AGREE AND CONTINUE".
22. Enter your personal and billing information and then click "START MY FREE TRIAL". Follow the prompt, click "GOT IT".
23. You should now be back to the "Cloud Speech-to-Text API" page. Click "ENABLE".
24. You should now be on the metrics page for the "Cloud Speech-to-Text API" page. In the far upper left corner, click
the hamburger icon (three horizontal lines). Hover over "APIs & Services" and click on "Credentials".
25. In the upper left, click on the "Create credentials" dropdown and select "Service account key".
26. In the "Service account" dropdown, select "App Engine default service account" and make sure that "JSON" is selected
as the key type. Click "Create". This will download a file. **Place this file somewhere safe that will not get uploaded
to any public repository. It can safely be placed in the `credentials` folder you made earlier.**
27. If you do not have Docker installed, please follow the
[Docker instruction documentation](https://docs.docker.com/install/). With Docker installed and with the still open
terminal, run the following commands:

```bash
cd deploy/
sudo bash build.sh
```

29. You will now have a Docker container built and ready to work on the project. If you have no pipeline running, you
can start a Docker image (an instance of the built Docker container) by running:

```bash
sudo bash run.sh
```

_**Note:** The above `run.sh` script also mounts the `cdptools` directory to the docker image, what this means is that
you will be able to edit the files both like normal on whichever editor you choose or in the bash terminal connected to
the docker image. The files are shared between the image and your system._

Once connected the Docker image, run:
```bash
pip install -e cdptools[all]
```

28. Once the dependencies are all installed, edit your configuration file for the system found at
`cdptools/configs/seattle-event-pipeline.json`. Specifically, change the filename for the credentials file to the name
of the credentials file you downloaded anywhere where there is the key `"credentials_path"` and change the file store
`"bucket_name"` to whatever your bucket address is.
29. To start a single gathering of events run:

```bash
run_cdp_pipeline EventGatherPipeline cdptools/configs/seattle-event-gather-pipeline.json
```

Or to run the pipeline every `n` minutes run:

```bash
run_cdp_pipeline EventGatherPipeline cdptools/configs/seattle-event-gather-pipeline.json --nm 20
```

In the above case, the pipeline will run every 20 minutes (`--nm 20`).

30. The pipeline is now running! You can leave it running by simply closing the terminal. To reconnect to a running
Docker container you can run:

```bash
sudo docker ps
```

To view all containers that are currently running.

Find the container you are looking for by image name, copy it's "CONTAINER ID" and then to reconnect run:
```bash
sudo docker attach e28e4954f626
```

Where your container id is replacing the `e28e4954f626`.

31. It may look like you haven't connected, but remember the pipeline is running on a schedule and won't print anything
to console unless it is currently processing data.

That wraps up how to create a development setup with full staging database, file store, and Google Cloud API enabled.
From here, if you wanted to develop a CDP instance for your own city, that would involve writing an `EventScraper`, and
changing the event pipeline configuration file.

It is a similar process for all other pipelines.

### Production Server Setup
The setup for a production server is nearly identical as for local development except for a couple of details:

1. Follow all the steps in described in the local development setup on a server from the host of your choice, except for
web interactions which can be done on any machine.
2. Because you are creating a production instance, probably best to not pre-pend the `stg-` to your project name.
3. It is recommended to not `git clone` the project repository and instead simply run
`pip install cdptools[seattle]` for a couple of reasons. First, not cloning the repository and removing the `-e`
means the code that is actually running is no longer editable, which for a production server is generally a good thing.
Second, specifying `seattle` over `all` means there will be less dependencies installed on the machine.

You may also need to ensure the bucket is "viewable" by `allUsers` on Google Cloud Console. Details [here](https://stackoverflow.com/questions/40232188/allow-public-read-access-on-a-gcs-bucket#answer-49809949).
If you want to have a front end for the system you will also need to allow CORS requests. Details [here](https://cloud.google.com/storage/docs/cross-origin).


## Running Pipelines
If you have made it this far in the deployment README, I applaud you. The last couple comments to add are about running
pipelines. Currently at `v2.0.0` launch of the project, the idea of _"backfilling"_ was pushed to a later date because
of how costly this can be (upwards of $10,000). Instead, pipelines at `v2.0.0` launch only have forward gathering,
in this case, CDP-Seattle, runs the `EventGatherPipeline` continuously on a high network speed, low CPU, low storage,
Google Cloud server every fifteen minutes and the `EventIndexPipeline` and `MinutesItemIndexPipeline` each on their own
servers but the same server configuration as the `EventGatherPipeline` every two days. These schedules can and should be
adjusted to fit your needs.

---
Now go make transparency research happen.
