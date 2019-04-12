docker run --rm \
    -it \
    --volume "$(dirname $(pwd))":/home/cdptools \
     cdp_test_bench \
     bash
