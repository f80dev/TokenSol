#Fichier docker d'installation du serveur

#effacer toutes les images : docker rmi $(docker images -a -q)
#effacer tous les containers : docker rm  $(docker ps -a -f status=exited -q)


#install docker :
#sudo curl -sSL get.docker.com | sh
#systemctl start docker
#systemctl enable --now docker
#configurer le firewall via cockpit aver ouverture des port pour mongoDB & 6800
#pour fedora 31 : https://linuxconfig.org/how-to-install-docker-on-fedora-31
#dnf install -y grubby && grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0" && reboot

#renouvellement des certificats
#désactiver le parefeu puis
#certbot certonly --standalone --email hhoareau@gmail.com -d server.f80lab.com
#cp /etc/letsencrypt/live/server.f80lab.com/* /root/certs

#fabrication: docker build -t f80hub/tokensol . && docker push f80hub/tokensol:latest
#installation: docker rm -f tokensol && docker pull f80hub/tokensol:latest
#Ouverture des ports : firewall-cmd --zone=public --add-port=4242/tcp
#démarrage prod : docker rm -f tokensol && docker pull f80hub/tokensol && docker run --restart=always -v /root/certs:/certs -p 4242:4242 --name tokensol -d f80hub/tokensol:latest python3 app.py 4242 ssl

#demarage sur windows :
# du main docker run --restart=always -p 4242:4242 --name tokensol -ti f80hub/tokensol:latest python3 app.py 4242
# analyse de l'image docker run --restart=always -p 4242:4242 --name tokensol -ti f80hub/tokensol:latest bash
#test en mode batch : docker run --restart=always -v /root/certs:/certs -p 4242:4242 --name tokensol -ti f80hub/tokensol:latest bash
#à tester avec la commande ./metaboss-ubuntu-latest update name --account GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy --keypair admin.json --new-name dudule

FROM python:3.9.0-buster

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME .

RUN pip3 -v install Flask
RUN pip3 -v install Flask-Cors
RUN pip3 -v install pyyaml
RUN pip3 install --upgrade pip setuptools wheel
RUN export PATH="$HOME/.local/bin:$PATH"
RUN pip3 install pyopenssl
RUN pip3 -v install solana
RUN pip3 -v install base58
RUN pip3 -v install ipfshttpclient
RUN pip3 -v install erdpy==1.4.0
RUN pip3 -v install ansi
RUN pip3 -v install -U secret-sdk
RUN pip3 -v install qrcode
RUN pip3 -v install pillow
RUN pip3 -v install py7zr
RUN pip3 -v install ffmpeg-python

WORKDIR /
RUN mkdir Solana
RUN mkdir Secret
RUN mkdir Elrond
RUN mkdir temp
RUN mkdir Configs
RUN mkdir Fonts
RUN mkdir ./Solana/Temp
RUN mkdir ./Solana/PEM
RUN mkdir ./Solana/Keys
RUN mkdir ./Secret/Keys
VOLUME /certs

EXPOSE 4242

COPY ./Fonts/*.ttf $APP_HOME/Fonts
COPY *.py $APP_HOME
COPY ./Solana/*.py $APP_HOME/Solana/
COPY ./Secret/*.py $APP_HOME/Secret/
COPY ./Elrond/*.py $APP_HOME/Elrond/
COPY ./Elrond/PEM/*.pem $APP_HOME/Elrond/PEM/
COPY ./Solana/Keys/*.json $APP_HOME/Solana/Keys/
COPY ./Solana/metaboss-ubuntu-latest $APP_HOME/Solana/
RUN chmod +x ./Solana/metaboss-ubuntu-latest

WORKDIR $APP_HOME/


CMD ["python3", "app.py","4242","ssl"]
