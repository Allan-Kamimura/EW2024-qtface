# arm64 or arm32
ARG IMAGE_ARCH=arm64

ARG BASE_VERSION=3.1.0

# "-vivante" or ""
ARG GPU="-vivante"

# app-name
ARG APP_ROOT="qt-face"

FROM --platform=linux/${IMAGE_ARCH} torizon/wayland-base${GPU}:${BASE_VERSION} AS opengles

ENV DEBIAN_FRONTEND="noninteractive"

# Install required packages for opengles
RUN apt-get update && apt-get install -y --no-install-recommends \
    libqt5gui5-gles libqt5quick5-gles && apt-get clean && apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

FROM --platform=linux/${IMAGE_ARCH} torizon/wayland-base${GPU}:${BASE_VERSION} AS Deploy

# Install required packages for Deploy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # Python
        python3-minimal \
        python3-venv \
        # PySide2
        python3-pyside2.qtwidgets \
        python3-pyside2.qtgui \
        python3-pyside2.qtcore \
        python3-pyside2.qtwebsockets \
        # Wayland
        qtwayland5 \
        # Miscellaneous
        imx-gpu-viv-wayland-dev \
        nano && \
    apt-get clean && apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

# Copy necessary files from opengles stage
COPY --from=opengles /usr/lib/aarch64-linux-gnu /usr2/lib/aarch64-linux-gnu

# Run rsync to copy the files to the desired location
RUN apt-get update && \
    apt-get install -y rsync && \
    rsync -a /usr2/lib/aarch64-linux-gnu /usr/lib/aarch64-linux-gnu && \
    rm -rf /usr2 && \
    apt-get remove -y rsync && \
    apt-get autoremove -y && \
    apt-get clean

# Create virtualenv
RUN python3 -m venv ${APP_ROOT}/.venv --system-site-packages

# Install pip packages on venv
COPY requirements-release.txt /requirements-release.txt
RUN . ${APP_ROOT}/.venv/bin/activate

USER torizon

# copy the source code
COPY /src ${APP_ROOT}/src

WORKDIR ${APP_ROOT}

ENV APP_ROOT=${APP_ROOT}
ENV QT_QPA_PLATFORM="wayland"