cd ./src
copy CNAME_debug CNAME
call ng build --configuration=debug --delete-output-path=true --source-map=true --optimization=false --output-hashing=none

cd ..
call gh-pages -d ./docs --repo https://github.com/f80dev/TokenSol.git -f -t true -b gh-pages -m "update from gh-pages"
echo "Mise en ligne du client terminé"

cd ./src
copy CNAM_prod CNAME

echo "Mise en place du serveur"
cd ../Server
docker build -t f80hub/tokensol .
docker push f80hub/tokensol:latest

cd ..
putty -pw %1 -ssh root@75.119.159.46 -m "install_server.txt"

echo "Traitement terminé"
