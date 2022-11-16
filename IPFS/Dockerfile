#build: docker build -t f80hub/ipfs-elrond . & docker push f80hub/ipfs-elrond:latest

#créer les directory : mkdir /root/ipfs/staging & mkdir /root/ipfs/data
#ouverture des ports :
#firewall-cmd --zone=public --add-port=5001/tcp --add-port=4001/tcp --add-port=8080/tcp
#firewall-cmd --zone=public --add-port=4001/tcp
#firewall-cmd --zone=public --add-port=8080/tcp
#prepare:   export ipfs_staging=/root/ipfs/staging
#           export ipfs_data=/root/ipfs/data
#update:docker rm -f ipfs_host && docker pull f80hub/ipfs-elrond
#run  : docker run -d --restart=always --name ipfs_host -v $ipfs_staging:/export -v $ipfs_data:/data/ipfs -p 4001:4001 -p 8080:8080 -p 5001:5001 ipfs/go-ipfs:latest
#debug: docker run -ti --name ipfs_host -v $ipfs_staging:/export -v $ipfs_data:/data/ipfs -p 4001:4001 -p 127.0.0.1:8080:8080 -p 127.0.0.1:5001:5001 f80hub/ipfs-elrond

FROM ipfs/go-ipfs:latest

EXPOSE 5001
EXPOSE 4001
EXPOSE 8080

RUN mkdir /root/export
RUN mkdir /root/data
RUN mkdir /root/data/ipfs

RUN ipfs daemon --init
RUN ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["http://75.119.159.46:5001", "http://localhost:3000", "http://127.0.0.1:5001", "https://webui.ipfs.io"]'
RUN ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["PUT", "POST"]'

