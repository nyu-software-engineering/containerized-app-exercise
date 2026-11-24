# Gesture Piano

![ML client CI](https://github.com/software-students-fall2026/containerized-app-exercise-mini-pekka/actions/workflows/ml-client.yml/badge.svg)
![Web app CI](https://github.com/software-students-fall2026/containerized-app-exercise-mini-pekka/actions/workflows/web-app.yml/badge.svg)

> **Note:** these badges stay broken until the `ml-client.yml` and `web-app.yml` workflows exist and have run once.

Gesture Piano is a simplified piano you play by making hand gestures in front of your webcam. Your left hand plays chords and your right hand plays the melody.

You open the app in your browser, hit Start, and hold your hands up to the camera. A machine learning client uses [MediaPipe] hand tracking to figure out what your hands are doing, turns that into chords and notes, and the browser plays them as piano. Everything you play gets saved to a database, and the dashboard shows your past sessions, a timeline of the chords you played, replays of old sessions, and some stats like your favorite chords.

We use MediaPipe's pretrained hand model and our own rules for turning hand poses into music.

[MediaPipe]: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker

## How to play

You pick a key and a scale (major or minor) in the settings bar, and both hands play notes from that scale.

**Left hand (chords).** Hold up fingers to pick a chord. The chord only plays after you hold a pose for a split second, which keeps it from flickering while you switch. It keeps playing until you change poses.

| Fingers out                | Scale degree | Chord in C major |
| -------------------------- | ------------ | ---------------- |
| Thumb                      | 1            | C                |
| Thumb, index               | 2            | Dm               |
| Thumb, index, middle       | 3            | Em               |
| Thumb, index, middle, ring | 4            | F                |
| All five                   | 5            | G                |
| Index, middle, ring, pinky | 6            | Am               |
| Middle, ring, pinky        | 7            | Bdim             |
| Ring, pinky                | 8            | C (high)         |
| Fist                       | none         | Silence          |

**Right hand (melody).** Eight note lanes run up the right side of the screen. Pinch your thumb and index finger together to play the note in that lane, and keep pinching to hold it. Open your hand to move between lanes without playing anything new.

**Stopping.** Make a fist, or move your hand out of the frame, and the sound stops.

## Team

- [Alissa Wu](https://github.com/alissawu)
- [Pope Cruz](https://github.com/pope-cruz)
- [Khidir Ahmed](https://github.com/khidirahmed)
- [Adil Inayat](https://github.com/ai2652-png)

## How it works

The app is three Docker containers that Docker Compose starts together:

- **`web-app`** is a Flask app. It serves the play page and the dashboard, passes camera frames to the ML client, and saves each session (start, stop, key and scale) to the database. It's the only part you open in your browser.
- **`ml-client`** is a small Flask API with no UI. It runs MediaPipe on each frame, works out the chord or note, and saves an event to the database whenever what you're playing changes.
- **`mongodb`** is the official MongoDB image. It stores the `sessions` and `events` collections.

The camera runs in your browser, not in a container. Docker on Mac and Windows can't get to your webcam. The browser sends about 15 frames a second to the web app, which forwards them to the ML client and sends back the result.

## Quick start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), installed and running
- [Git](https://git-scm.com/downloads)
- A webcam and a recent version of Chrome, Firefox, Edge or Safari

### Run the app

1.  Clone the repo and move into it:

    ```shell
    git clone https://github.com/software-students-fall2026/containerized-app-exercise-mini-pekka.git
    cd containerized-app-exercise-mini-pekka
    ```

2.  Make your `.env` file by copying the example. On Mac or Linux, run:

    ```shell
    cp env.example .env
    ```

    On Windows (PowerShell), run:

    ```powershell
    Copy-Item env.example .env
    ```

    The example values work as-is for running on your own computer. See [Environment variables](#environment-variables) for what each one does.

3.  Build and start all three containers:

    ```shell
    docker compose up --build
    ```

    The first build downloads MediaPipe and takes a few minutes.

4.  Go to <http://localhost:5000> in your browser and allow camera access when it asks.

    Use `localhost` exactly. Browsers only allow camera access on `localhost` or over HTTPS, and your computer's IP address won't work.

    If Docker says port 5000 is already in use and you're on a Mac, it's probably AirPlay Receiver. Turn it off in System Settings > General > AirDrop & Handoff, then run `docker compose up` again.

5.  To stop the app, press `Ctrl+C` in that terminal, then run:

    ```shell
    docker compose down
    ```

    Saved sessions are kept between runs. To wipe the database completely, use `docker compose down -v` instead.

### Load sample data

The dashboard is empty until you play something. To fill it with some sample sessions, run this while the app is running:

```shell
docker compose exec ml-client python seed.py
```

To remove the sample sessions (your own sessions stay), run:

```shell
docker compose exec ml-client python seed.py --clear
```

## Environment variables

All the settings live in one `.env` file in the repo root, which every container reads. 
`.env` is gitignored. The repo has an `env.example` with the same keys and dummy values, and we sent the course admins the real contents separately.

| Variable                     | What it's for                                         | Example value                                             |
| ---------------------------- | ----------------------------------------------------- | --------------------------------------------------------- |
| `MONGO_INITDB_ROOT_USERNAME` | Username MongoDB creates the first time it starts     | `admin`                                                   |
| `MONGO_INITDB_ROOT_PASSWORD` | Password for that user                                | `secret`                                                  |
| `MONGO_URI`                  | How the two Flask apps connect to MongoDB             | `mongodb://admin:secret@mongodb:27017/?authSource=admin`  |
| `MONGO_DBNAME`               | Name of the database the app uses                     | `gesture_piano`                                           |
| `ML_CLIENT_URL`              | Where the web app sends camera frames                 | `http://ml-client:5001`                                   |

The username and password in `MONGO_URI` have to match the two `MONGO_INITDB_*` values. MongoDB only creates that user the first time it starts with an empty database. Changing the username or password later means running `docker compose down -v` to reset the database, which also deletes your saved sessions.

## Development

Each part (`web-app` and `machine-learning-client`) has its own Pipfile and is set up separately.

### Set up a virtual environment

You need Python 3.12 and [pipenv]. Then, from inside the part you're working on:

```shell
cd web-app
pipenv install --dev
```

Do the same in `machine-learning-client` if you're working on that. MediaPipe doesn't install on Intel Macs, so on one of those you can only run the ML client in Docker.

[pipenv]: https://pipenv.pypa.io/en/latest/installation.html

### Run the tests and lint

Tests are in each part's `tests` folder. They use [mongomock] instead of a real database and fake the ML client, so no containers need to be running. From inside `web-app` or `machine-learning-client`:

```shell
pipenv run pytest --cov
pipenv run black .
pipenv run pylint *.py tests/*.py
```

Both parts need to stay at 80% test coverage or above, and CI checks [black] and [pylint] on every PR.

[mongomock]: https://github.com/mongomock/mongomock
[black]: https://black.readthedocs.io/en/stable/
[pylint]: https://pylint.readthedocs.io/en/stable/
