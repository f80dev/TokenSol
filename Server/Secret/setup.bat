secretcli config chain-id secret-4
secretcli config output json
secretcli config node http://api.scrt.network:26657


#Create account https://docs.scrt.network/cli/secretcli.html#keys

./secretcli keys add paul
./secretcli keys export paul > ./Keys/paul.secretkey

./secretcli keys add roger
./secretcli keys export roger > ./Keys/roger.secretkey

./secretcli keys list
