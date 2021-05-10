DO_LOCAL=1 # default false
DO_STATIC=1 # default false
BUILD_CFG=./build/Dockerfile
BUILD_TAG=ushift-build
SRC_ROOT=$(shell pwd)
BIN=./_output/bin/ushift

CTR_CMD=$(or $(shell which podman), $(shell which docker))
CACHE_VOL=go_cache

CGO_ENABLED=1
STATIC_OPTS=
ifeq ($(DO_STATIC), 0)
STATIC_OPTS=--ldflags '-extldflags "-static"'
CGO_ENABLED=0
endif

all: build

.PHONY: build_local
build_local:
	 GOOS=linux GARCH=amd64 CGO_ENABLED=$(CGO_ENABLED) go build $(STATIC_OPTS) -mod vendor  -o _output/bin/ushift cmd/main.go

.PHONY: .init
.init:
	$(CTR_CMD) volume create --label name=ushift-build $(CACHE_VOL)
	$(CTR_CMD) build -t $(BUILD_TAG) -f $(BUILD_CFG) ./build

.PHONY: build_ctr
build_ctr: .init
	$(CTR_CMD) run -v $(CACHE_VOL):/mnt/cache -v $(SRC_ROOT):/opt/app-root/src/github.com/microshift: $(BUILD_TAG)

.PHONY: build
ifeq ($(DO_LOCAL), 0)
build: build_local
else
build: build_ctr
endif

clean:
	rm -f _output/bin/ushift
ifdef CTR_CMD
	$(CTR_CMD) system prune --filter label=name=ushift-build -f
endif
