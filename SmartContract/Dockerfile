#Arreter tous les conteneurs:  docker stop $(docker ps -a -q)
#Effacer toutes les images : docker rm $(docker ps -a -q)

#Utiliser ERDPY depuis windows
#directement inspiré de https://github.com/erdDEVcode/erdnet/blob/master/Dockerfile

FROM ubuntu:jammy
#fabrication de l'image pour X86: docker build -t f80hub/elrond-dev . & docker push f80hub/elrond-dev
#déploiement : docker rm -f elrond-dev && docker pull f80hub/elrond-dev:latest
#ligne de commande : docker rm -f elrond-dev && docker run --name elrond-dev -v C:/Users/hhoar/IdeaProjects/NFTCalvi/SmartContract:/home/erd/dev/ -ti f80hub/elrond-dev bash

RUN apt update
RUN apt upgrade
RUN apt install -y wget python3 python3-venv sudo build-essential nano net-tools python3-pip
RUN apt install -y libncurses5
RUN pip3 install wheel

RUN adduser --home /home/erd --shell /bin/bash --disabled-password erd
RUN echo "erd ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER erd

WORKDIR /home/erd
RUN wget -O erdpy-up.py https://raw.githubusercontent.com/ElrondNetwork/elrond-sdk-erdpy/main/erdpy-up.py
RUN python3 erdpy-up.py

ENV PATH="/home/erd/elrondsdk/:${PATH}"
RUN pip install erdpy==2.0.3

WORKDIR /home/erd/dev

CMD ["bash","source","/home/erd/elrondsdk/erdpy-activate"]
