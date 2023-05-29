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
#Pour le server F80: certbot certonly --standalone --email hhoareau@gmail.com -d server.f80lab.com && cp /etc/letsencrypt/live/server.f80lab.com/* /root/certs
#Pour le serveur NFluent: certbot certonly --standalone --email hhoareau@gmail.com -d api.nfluent.io && cp /etc/letsencrypt/live/api.nfluent.io/* /root/certs
#cp /etc/letsencrypt/live/server.f80lab.com/* /root/certs
#cp /etc/letsencrypt/live/api.nfluent.io/* /root/certs

#fabrication: docker build -t f80hub/tokensol . && docker push f80hub/tokensol:latest
#installation: docker rm -f tokensol && docker pull f80hub/tokensol:latest
#Ouverture des ports : firewall-cmd --zone=public --add-port=4242/tcp ou ufw allow 4242/tcp
#démarrage prod : docker rm -f tokensol && docker pull f80hub/tokensol && docker run --restart=always -v /root/Configs:/Configs -v /root/Fonts:/Fonts -v /root/Operations:/Operations -v /root/temp:/temp -v /root/certs:/certs -p 4242:4242 --name tokensol -d f80hub/tokensol:latest python3 wsgi.py devConfig ssl



#demarage sur windows :
# du main docker run --restart=always -p 4242:4242 -v /root/temp:/temp -v /root/certs:/certs --name tokensol -ti f80hub/tokensol:latest python3 flaskr/api.py 4242
# analyse de l'image docker run --restart=always -p 4242:4242 --name tokensol -ti f80hub/tokensol:latest bash
#test en mode batch : docker run --restart=always -v /root/temp:/temp -v /root/certs:/certs -p 4242:4242 --name tokensol -ti f80hub/tokensol:latest bash
#à tester avec la commande ./metaboss-ubuntu-latest update name --account GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy --keypair admin.json --new-name dudule

#Installation d'un serveur
#il faut créer les répertoire
#mkdir /root/Server
#mkdir /root/Server/Configs
#mkdir /root/Server/Fonts
#mkdir /root/Server/Operations

#Execution sur le serveur de production :
#docker rm -f tokensol && docker pull f80hub/tokensol
#docker run --restart=always -v /root/Server/Configs:/Configs -v /root/Server/Fonts:/Fonts -v /root/Server/Operations:/Operations -v /root/Server/temp:/temp -v /root/certs:/certs -p 4242:4242 --name tokensol -d f80hub/tokensol:latest python3 wsgi.py prodConfig debug ssl

#Version pour PC
FROM python:3.9.0-buster


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME .

RUN export PATH="$HOME/.local/bin:$PATH"

RUN pip3 -v install Flask
RUN pip3 -v install Flask-Cors
RUN pip3 -v install pyyaml
RUN pip3 -v install --upgrade pip setuptools wheel

RUN pip3 -v install solana
RUN pip3 -v install base58
RUN pip3 -v install ipfshttpclient
RUN pip3 -v install ansi
RUN pip3 -v install -U secret-sdk
RUN pip3 -v install pyqrcode
RUN pip3 -v install pillow
RUN pip3 -v install py7zr
RUN pip3 -v install ffmpeg-python
RUN pip3 -v install pypng
RUN pip3 -v install dnspython
RUN pip3 -v install pymongo
RUN pip3 -v install google-cloud-storage
RUN pip3 -v install PyGithub
RUN pip3 -v install fonttools
RUN pip3 -v install numpy
RUN pip3 -v install svglib
RUN pip3 -v install pycairo
RUN pip3 -v install imageio
RUN pip3 -v install bip_utils
RUN pip3 -v install matplotlib
RUN pip3 -v install Unidecode
RUN pip3 -v install xmltodict
RUN pip3 -v install pypng
RUN pip3 -v install flask-jwt-extended
RUN pip3 -v install apscheduler
RUN pip3 -v install Flask-Caching
RUN pip3 -v install requests-cache
RUN pip3 -v install cryptography==40.0.0
RUN pip3 -v install networkx
RUN pip3 -v install flask-socketio
RUN pip3 -v install simple-websocket
RUN pip3 -v install eth-account
RUN pip3 -v install py-solc-x
RUN pip3 -v install web3
RUN pip3 -v install pandas
RUN pip3 -v install rembg
RUN pip3 -v install multiversx-sdk-core
RUN pip3 -v install multiversx-sdk-wallet
RUN pip3 -v install multiversx-sdk-network-providers
RUN pip3 -v install pyopenssl
RUN pip3 -v install openpyxl
RUN pip3 -v install mega.py

WORKDIR /
RUN mkdir Solana
RUN mkdir Secret
RUN mkdir Elrond
RUN mkdir Polygon
RUN mkdir temp
RUN mkdir Configs
RUN mkdir Fonts
RUN mkdir Operations
RUN mkdir flaskr
RUN mkdir flaskr/static

RUN mkdir ./Solana/Temp
RUN mkdir ./Elrond/PEM
RUN mkdir ./Polygon/Keys
RUN mkdir ./Polygon/Master

RUN mkdir ./Solana/Keys
RUN mkdir ./Secret/Keys
VOLUME /certs

EXPOSE 4242

COPY *.py $APP_HOME
COPY secret_key $APP_HOME
COPY *.json $APP_HOME
COPY *.yaml $APP_HOME
COPY *.html $APP_HOME
COPY ./flaskr/*.py $APP_HOME/flaskr/
COPY ./flaskr/static/* $APP_HOME/flaskr/static/
COPY ./Solana/*.py $APP_HOME/Solana/
COPY ./Polygon/*.py $APP_HOME/Polygon/
COPY ./Secret/*.py $APP_HOME/Secret/
COPY ./Elrond/*.py $APP_HOME/Elrond/

COPY ./Elrond/PEM/*.pem $APP_HOME/Elrond/PEM/
COPY ./Elrond/PEM/*.json $APP_HOME/Elrond/PEM/
COPY ./Polygon/Keys/*.secret $APP_HOME/Polygon/Keys/
COPY ./Polygon/Master/contracts $APP_HOME/Polygon/Master/contracts/
COPY ./Polygon/Master/node_modules/@openzeppelin $APP_HOME/Polygon/Master/node_modules/@openzeppelin

COPY ./Solana/Keys/*.json $APP_HOME/Solana/Keys/
COPY ./Solana/metaboss-ubuntu-latest $APP_HOME/Solana/
COPY ./Configs/*.yaml $APP_HOME/Configs/
COPY ./Operations/*.yaml $APP_HOME/Operations/
RUN chmod +x ./Solana/metaboss-ubuntu-latest

WORKDIR $APP_HOME

CMD ["python3", "wsgi.py","devConfig","ssl"]
