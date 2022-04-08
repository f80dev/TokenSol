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

#fabrication: docker build -t f80hub/tokensol . & docker push f80hub/tokensol:latest
#installation: docker rm -f tokensol && docker pull f80hub/tokensol:latest
#Ouverture des ports : firewall-cmd --zone=public --add-port=9999/tcp
#démarrage prod : docker rm -f tokensol && docker pull f80hub/tokensol && docker run --restart=always -v /root/certs:/certs -p 9999:9999 --name tokensol -d f80hub/tokensol:latest python3 app.py 9999 ssl

#demarage sur windows : docker run --restart=always -p 9999:9999 --name tokensol -ti f80hub/tokensol:latest python3 app.py 9999
#test en mode batch : docker run --restart=always -v /root/certs:/certs -p 9999:9999 --name tokensol -ti f80hub/tokensol:latest bash
#à tester avec la commande ./metaboss-ubuntu-latest update name --account GwCtQjSZj3CSNRbHVVJ7MqJHcMBGJJ9eHSyxL9X1yAXy --keypair admin.json --new-name dudule

FROM python:3.9.0-buster


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 -v install Flask
RUN pip3 -v install Flask-Cors
RUN pip3 -v install pyyaml
RUN pip3 install --upgrade pip setuptools wheel
RUN export PATH="$HOME/.local/bin:$PATH"
RUN pip3 install pyopenssl
RUN pip3 -v install solana

WORKDIR /
RUN mkdir temp
VOLUME /certs

COPY *.py $APP_HOME/
COPY *.json $APP_HOME/
COPY metaboss-ubuntu-latest $APP_HOME/

WORKDIR $APP_HOME/
RUN chmod +x metaboss-ubuntu-latest

CMD ["python3", "app.py","9999","ssl"]
