docker run \
    --rm \
    -it \
    --volume "$(dirname $(pwd))":/home/cdptools \
     cdptools \
     bash
