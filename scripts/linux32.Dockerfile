FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git curl build-essential gcc-multilib g++-multilib clang libclang-dev llvm-dev cmake ninja-build pkg-config nasm file python3 patchelf \
    libgtk-3-dev:i386 libayatana-appindicator3-dev:i386 libasound2-dev:i386 libpulse-dev:i386 libxdo-dev:i386 libxfixes-dev:i386 libxcb-randr0-dev:i386 libxcb-shape0-dev:i386 libxcb-xfixes0-dev:i386 \
    libgstreamer1.0-dev:i386 libgstreamer-plugins-base1.0-dev:i386 libssl-dev:i386 libdbus-1-dev:i386 libopus-dev:i386 libvpx-dev:i386 libyuv-dev:i386 libaom-dev:i386 libva-dev:i386 \
    xvfb xauth xdotool imagemagick dbus-x11 && rm -rf /var/lib/apt/lists/*
RUN mkdir /opt/pkgconfig && printf 'prefix=/usr\nlibdir=/usr/lib/i386-linux-gnu\nincludedir=/usr/include\nName: libyuv\nDescription: system libyuv\nVersion: 1\nLibs: -L${libdir} -lyuv\nCflags: -I${includedir}\n' > /opt/pkgconfig/libyuv.pc
ENV PKG_CONFIG_ALLOW_CROSS=1 PKG_CONFIG_PATH=/opt/pkgconfig PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig
ENV CARGO_TARGET_I686_UNKNOWN_LINUX_GNU_LINKER=gcc CFLAGS_i686_unknown_linux_gnu=-m32 CXXFLAGS_i686_unknown_linux_gnu=-m32
ENV CARGO_PROFILE_RELEASE_LTO=false CARGO_PROFILE_RELEASE_CODEGEN_UNITS=16 CARGO_BUILD_JOBS=3
ENV PATH=/root/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /src
