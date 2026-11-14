# TrueGaze in a container: Blender 4.5 LTS (the pinned version), ffmpeg and the Python tools.
# Renders on the CPU here (no Metal or GPU in the container), so final quality is slow; use "draft" to check the pipeline.
#   docker build -t truegaze .
#   docker run --rm -v "$PWD/outputs:/app/outputs" truegaze                 # ./reproduce.sh draft
#   docker run --rm -v "$PWD/outputs:/app/outputs" truegaze ./reproduce.sh  # final quality
# Blender ships Linux builds for x86-64 only; on Apple silicon this runs emulated (slow).
FROM --platform=linux/amd64 python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg xz-utils curl ca-certificates libgl1 libxi6 libxrender1 libxkbcommon0 libsm6 libxfixes3 libxxf86vm1 libegl1 \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://download.blender.org/release/Blender4.5/blender-4.5.16-linux-x64.tar.xz | tar -xJ -C /opt \
    && ln -s /opt/blender-4.5.16-linux-x64/blender /usr/local/bin/blender
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["./reproduce.sh", "draft"]
