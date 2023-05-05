import {HostListener, Injectable, OnInit} from '@angular/core';
import {
    clusterApiUrl,
    Connection,
    PublicKey,
} from "@solana/web3.js";
import {TOKEN_PROGRAM_ID} from "@solana/spl-token";
import * as SPLToken from "@solana/spl-token";
import {HttpClient, HttpErrorResponse} from "@angular/common/http";
import {$$, CryptoKey, encrypt, words} from "../tools";
import {environment} from "../environments/environment";

import {catchError, fromEvent, retry, Subject, throwError, timeout} from "rxjs";
import {Collection, Operation} from "../operation";
import {NFT, SolanaToken, SplTokenInfo, Validator} from "../nft";
import {Configuration, Layer} from "../create";
import {Router} from "@angular/router";



@Injectable({
    providedIn: 'root'
})
export class NetworkService implements OnInit {
    unity_conversion: any={};
    private _network:string="";
    private _connection: Connection=new Connection(clusterApiUrl("devnet"), 'confirmed');
    waiting: string="";
    complement: string | undefined ="";
    fiat_unity: string="$";
    version: string="0.1";

    network_change=new Subject<string>();
    config_loaded=new Subject<any>();

    server_nfluent: string=environment.server;
    online: boolean=true;
    keys:CryptoKey[]=[];
    config:any={};
    networks_available:string[]=[];          //network
    stockage_available:string[]=[];          //stockage visuel et metadata
    stockage_document_available:string[]=[]; //stockage document attaché

    chain_id="D"                               //Chain_id du réseau elrond

    constructor(
        private httpClient : HttpClient
    ) {
        this.info_server().subscribe((r:any)=>{
            this.config=r;
            this.config_loaded.next(r);
        })
    }

    @HostListener('online', ['$event'])
    switch_online(e:any){
        this.online=(e.type=='online');
    }

    @HostListener('offline', ['$event'])
    switch_offline(e:any){
        this.online=(e.type=='online');
    }


    ngOnInit(): void {

    }

    find_key_by_address(addr:string) : CryptoKey | undefined {
        for(let k of this.keys){
            if(k.address==addr)return k;
        }
        return undefined
    }


    init_keys(with_balance=false,access_code:string="",operation_id:string="") {
        return new Promise((resolve, reject) => {
            this.wait("Chargement des clés");
            this.httpClient.get<CryptoKey[]>(this.server_nfluent + "/api/keys/?access_code="+access_code+"&network=" + this.network + "&with_private=true&with_balance="+with_balance+"&operation="+operation_id,).subscribe((r: CryptoKey[]) => {
                this.keys = r;
                this.wait();
                resolve(r);
            },(err:any)=>{
                this.wait("!Probléme de chargement");
                $$("Probleme de chargement");
                reject();
            });
        });
    }

    add_key(key:any,network="elrond-devnet",email=""){
        return this.httpClient.post(this.server_nfluent+"/api/keys/"+key["name"]+"/?network="+network+"&email="+email,key);
    }


    // update(nft_addr:string,new_value:string,field="uri",network="elrond-devnet") {
    //   return new Promise((resolve, reject) => {
    //     if(field=='uri'){
    //       this.httpClient.get(this.network.server_nfluent+"/api/update?url="+new_value+"&account="+this.user.key+"&network="+network).subscribe((r:any)=>{
    //         resolve(true);
    //       })
    //     }
    //   });
    // }

    //
    // update_obj(nft_addr:string,data:any,network="elrond-devnet") {
    //   return new Promise((resolve, reject) => {
    //     this.httpClient.post(this.network.server_nfluent+"/api/update_obj/?account="+nft_addr+"&keyfile="+this.user.key?.name+"&network="+network,data).subscribe((r:any)=>{
    //       if(r.result=="error")
    //         reject(r.error);
    //       else
    //         resolve(r.out);
    //     })
    //   });
    // }


    burn(nft_addr:string | undefined,key:string,network="elrond-devnet",delay=1) {
        return new Promise((resolve, reject) => {
            this.wait("En cours de destruction");
            this.httpClient.get(this.server_nfluent+"/api/burn?&delay="+delay+"&account="+nft_addr+"&keyfile="+key+"&network="+network).subscribe((r:any)=>{
                this.wait("");
                if(r.result=="error")
                    reject(r.error);
                else
                    resolve(r.out);
            })
        });
    }

    sign(nft_addr:string,creator_addr:string,key:CryptoKey, network="elrond-devnet") {
        return new Promise((resolve, reject) => {
            this.httpClient.get(this.server_nfluent+"/api/sign?creator="+creator_addr+"&account="+nft_addr+"&keyfile="+key?.name+"&network="+network).subscribe((r:any)=>{
                resolve(r);
            },(err)=>{
                reject(err);
            });
        });
    }


    use(address: string, network: string,key:CryptoKey) {
        return new Promise((resolve, reject) => {
            this.httpClient.get(this.server_nfluent+"/api/use?account="+address+"&keyfile="+key.name+"&network="+network).subscribe((r:any)=>{
                resolve(r);
            },(err)=>{
                reject(err);
            });
        });
    }

    del_key(name: string) {
        return this.httpClient.delete(this.server_nfluent+"/api/keys/"+name+"/?network="+this.network)
    }


    archive(tokens: any) {
        return new Promise((resolve, reject) => {
            this.httpClient.post(this.server_nfluent+"/api/export/",tokens).subscribe((r)=>{
                resolve(r);
            },(err)=>{
                reject(err);
            })
        });
    }

    encrypte_key(name:string,network:string,privateKey="") {
        let body={secret_key:privateKey,alias:name}
        return this._post("encrypt_key/"+network+"/","",body)
    }

    //
    // get_tokens(pubkey: PublicKey,f:Function) {
    //     return new Promise((resolve, reject) => {
    //         f(pubkey, {programId: TOKEN_PROGRAM_ID})
    //             .then((r:any) => {
    //                 let rc = [];
    //                 for (let t of r.value) {
    //                     rc.push(t);
    //                 }
    //                 resolve(rc);
    //             }).catch((err:Error)=>{reject(err)});
    //     });
    // };

    get_token(addr:string,network:string){
        return this._get("tokens/"+addr+"/","network="+network);
    }

    get network(): string {
        return this._network;
    }

    set network(network_name: string) {
        this.init_network(network_name)
    }

    init_network(network:string) : Promise<any>{
        return new Promise((resolve) => {
            if(this._network==network && this.keys.length>0){
                resolve(this.keys)
            } else {
                this._network=network;
                if(this.isMain())this.chain_id="T"; else this.chain_id="D";
                this.init_keys(true).then(()=>{
                    this.network_change.next(network);
                    resolve(this.keys);
                }).catch(()=>{resolve(null)})
            }
        });
    }

    get connection(): Connection {
        return this._connection;
    }

    set connection(value: Connection) {
        this._connection = value;
    }



    add_solscan(token:any) : any{
        for(let k in token){
            let value=token[k];
            if(value && typeof value==="object" && value.constructor.name === "PublicKey"){
                value='https://solscan.io/address/'+value.toBase58()+'?cluster='+this._network;
                token[k+"_explorer"]=value;
            }
        }
        return token;
    }


    create_token(offchain:any,mintAuthority:string,mintAddress:string,data_sup:any,splMintInfo:any,splTokenInfo:SplTokenInfo):SolanaToken {
        let token:SolanaToken = {
            search:{collection:"",metadata:""},
            address: mintAddress,
            network:this.network,
            metadataPDA: {},
            mint: mintAuthority,
            splMintInfo: splMintInfo,
            splTokenInfo: splTokenInfo,
            metadataOffchain: offchain,
            metadataOnchain:{
                key:0,
                updateAuthority:"",
                mint:"",
                data:data_sup,
                primarySaleHappened:0,
                isMutable:1,
                type:"metaplex"
            }
        }
        if(offchain && offchain.hasOwnProperty("attributes")){
            token.search={collection:words(offchain.collection),metadata:words(Object.values(offchain.attributes))}
        }

        return token;
    }


    solscan_info(mintAddress:string){
        let explorer_domain=(this.network=="solana-devnet" ? "https://api-devnet.solscan.io" : "https://api.solscan.io")
        return new Promise((resolve, reject) => {
            if(mintAddress){
                this.httpClient.get(explorer_domain+"/account?address=" + mintAddress).subscribe((dt: any) => {
                    this.connection.getAccountInfo(new PublicKey(dt.data.tokenInfo.tokenAuthority), "confirmed").then((resp: any) => {
                        let owner = resp.owner.toBase58();
                        dt.owner=owner;
                        resolve(dt);
                    },(err:any)=>{$$("erreur ",err);reject(err);})
                });
            }
        });
    }




    get_price(unity="egld"){
        return new Promise((resolve, reject) => {
            let now=new Date().getTime();
            if(this.unity_conversion && this.unity_conversion.hasOwnProperty(unity) && now-this.unity_conversion[unity].lastdate<100000){
                resolve(this.unity_conversion[unity].value);
            }
            if(unity.toLowerCase()=="egld"){
                this.httpClient.get("https://data.elrond.com/market/quotes/egld/price").subscribe((result:any)=>{
                    if(result.length>0){
                        this.unity_conversion[unity]={value:result[result.length-1].value,lastdate:new Date().getTime()};
                        resolve(result[result.length-1].value);
                    }
                },(err)=>{
                    reject(80);
                });
            } else {
                this.unity_conversion[unity]={value:1,lastdate:new Date().getTime()};
                //TODO a adapter sur la base d'un tableau de correspondance entre la monnaie
                resolve(1);
            }
        });

    }


    build_token_from_solscan(mintAddress:string):Promise<SolanaToken> {
        return new Promise((resolve, reject) => {
            this.solscan_info(mintAddress).then((dt:any)=>{
                if(!dt.data?.hasOwnProperty("metadata")){
                    reject("NFT introuvable");
                } else {
                    let url_metadata=dt.data?.metadata?.data.uri;
                    let owner="";
                    let mintAuthority=dt;
                    let splTokenInfo:SplTokenInfo={
                        address: mintAddress, amount: 0, isFrozen: false, mint: "", owner: owner, state: 0
                    };

                    if(dt.data.metadata.primarySaleHappened==0)owner=dt.data.metadata.updateAuthority;
                    this.httpClient.get(url_metadata).subscribe((offchain:any)=>{
                        resolve(this.create_token(offchain,mintAuthority,dt.data.metadata.mint,dt.data,dt.data.tokenInfo,splTokenInfo));
                    })
                }
            })
        });
    }


    complete_token(owner:string,e:any,filter:any=null,short=false) : Promise<any> {
        $$("Completion des tokens");
        return new Promise((resolve, reject) => {
            let rc: any={};

            if(e.account && e.account.data){
                let splTokenInfo:any = SPLToken.AccountLayout.decode(e.account.data);
                let mintAddress=splTokenInfo.mint.toBase58();

                splTokenInfo["address"] = e.address;
                let layoutInfo = SPLToken.MintLayout.decode(e.account.data);
                let mintAuthority=layoutInfo.mintAuthority.toBase58();
                splTokenInfo.amount=Number(splTokenInfo.amount);

                if(filter==null || (filter.mintAuthority && mintAuthority==filter.mintAuthority)){
                    $$("Analyse de "+mintAddress);
                    this.httpClient.get(this.server_nfluent+"/api/scan/"+mintAddress+"?network="+this.network).subscribe((token_account:any)=>{
                        if(token_account && token_account.hasOwnProperty("uri")){
                            let headers = new Headers({
                                'Cache-Control':  'no-cache, no-store, must-revalidate, post-check=0, pre-check=0',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            });

                            //Impossible d'avoir le résultat de suite : https://stackoverflow.com/questions/46551413/github-not-update-raw-after-commit
                            let url=token_account.uri+"?ts="+Date.now();
                            $$("Ouverture de "+url);
                            // @ts-ignore
                            this.httpClient.get(url,{headers: headers}).pipe(retry(3),timeout(5000)).subscribe((offchain:any)=>{
                                resolve(this.create_token(offchain,mintAuthority,mintAddress,token_account,layoutInfo,splTokenInfo));
                            },(err:any)=>{
                                $$("Anomalie à la lecture des métadata sur "+token_account.uri,err);
                                resolve(this.create_token({},mintAuthority,mintAddress,token_account,layoutInfo,splTokenInfo));
                            })
                        } else {
                            reject();
                        }
                    },(err)=>{reject(err);})
                }
            }
        });
    }


    isMain() {
        return this._network.indexOf("mainnet")>-1;
    }



    private handleError(error: HttpErrorResponse) {
        if (error.status === 0) {
            // A client-side or network error occurred. Handle it accordingly.
            console.error('An error occurred:', error.error);
        } else {
            // The backend returned an unsuccessful response code.
            // The response body may contain clues as to what went wrong.
            if(error.statusText === "TimeoutError"){
                this.online=false;
            }
        }
        // Return an observable with a user-facing error message.
        return throwError(() => new Error('Problème technique. Serveur probablement injoignable'));
    }

    _get(url: string, param: string="",_timeout=30000) {
        if(!url.startsWith("http")){
            url="/api/"+url;
            url=this.server_nfluent+url.replace("//","/").replace("/api/api/","/api/")
        }
        return this.httpClient.get<any>(url+"?"+param).pipe(retry(1),timeout(_timeout),catchError(this.handleError))
    }


    _post(url: string, param: string="",body={},_timeout=30000) {
        if(!url.startsWith("http")){
            url="/api/"+url;
            url=this.server_nfluent+url.replace("//","/").replace("/api/api/","/api/")
        }
        return this.httpClient.post<any>(url+"?"+param,body).pipe(retry(1),timeout(_timeout),catchError(this.handleError))
    }



    get_tokens_from(type_addr:string,addr:string,limit=100,with_attr=true,filter:any=null,offset=0,network="elrond-devnet") : Promise<{result:any[],offset:number}> {

        $$("Recherche de token par "+type_addr)
        return new Promise((resolve,reject) => {
            if(addr==null){
                reject();
            } else {
                if(this.network.indexOf("solana")>-1){
                    let func:any=null;

                    if(type_addr=="owner"){
                        this.httpClient.get(this.server_nfluent+"/api/nfts/?with_attr="+with_attr+"&limit="+limit+"&offset="+offset+"&account="+addr+"&network="+this.network).subscribe((r:any)=>{
                            resolve(r);
                        })
                    }

                    if(type_addr=="token"){
                        this.build_token_from_solscan(addr).then((token:SolanaToken)=>{
                            resolve({result:[token],offset:0});
                        }).catch((err)=>{
                            reject(err);
                        });
                        return;
                    }

                }

                if(this.network.indexOf("elrond")>-1 || this.network.indexOf("polygon")>-1 || this.network.startsWith("db-")){
                    this.httpClient.get(this.server_nfluent+"/api/nfts/?limit="+limit+"&with_attr="+with_attr+"&offset="+offset+"&account="+addr+"&network="+this.network).subscribe((r:any)=>{
                        resolve({result:r,offset:offset});
                    },(err:any)=>{
                        reject(err);
                    })
                }


                if(type_addr=="miner"){
                    //TODO function en chantier
                    this.httpClient.get(this.server_nfluent+"/api/token_by_delegate/?account="+addr+"&network="+this.network).subscribe((r:any)=> {
                        this.complete_token(addr,r.value).then(r => {
                            resolve(r);
                        })
                    });
                }


            }
        });
    }

    get_nfts_from_miner(miner:PublicKey) : Promise<any[]> {
        return new Promise((resolve,reject) => {
            this.connection.getProgramAccounts(miner,"confirmed").then((r:any)=>{
                this.complete_token(miner.toBase58(),r.value).then(r=>{resolve(r);})
            })
        });
    }

    installed_wallet(){
        let rc=[];
        // @ts-ignore
        if(window.hasOwnProperty("phantom"))rc.push("phantom");
        // @ts-ignore
        if(window.hasOwnProperty("solflare"))rc.push("solflare");
        // @ts-ignore
        if(window.hasOwnProperty("elrondWallet"))rc.push("maiar");
        return rc;
    }

    wait(message: string="",durationInSec=1000) {
        this.waiting=message;
        setTimeout(()=>{this.waiting=""},durationInSec*1000);
    }

    isElrond(addr="") {
        if(addr==null)return false;
        if(addr.length==0){
            if(!this.network)return false;
            return this.network.indexOf("elrond")>-1;
        } else {
            return addr.startsWith("erd");
        }
    }

    isSolana(network="") {
        if(network=="")network=this.network;
        return network.indexOf("solana")>-1;
    }

    isPolygon(network="") {
        if(network=="")network=this.network;
        return network.indexOf("polygon")>-1;
    }

    get_nfts_balance_from_ftx(){
        return this.httpClient.get("https://ftx.us/api/nft/balances")
    }

    private get_tokens_from_ftx(filter: string) {
        return new Promise((resolve,reject) => {

            let key="solMintAddress";
            let value="!none";
            if(filter.length<40 || filter.length>50){
                key="collection";
                value=filter;
            }
            let url=this.server_nfluent+"/api/ftx/tokens/";
            $$("recherche sur "+url);
            this.httpClient.get(url).subscribe(((r:any)=>{
                let rc:any[]=[];
                $$(r.results.length+" NFTs identifié, croisement avec "+filter+" sur la collection");
                for(let token of r.results){
                    if(filter.length==0 || token.collection.indexOf(filter)>-1)
                        rc.push(token);
                }
                resolve(rc);
            }),(err)=>{
                reject(err);
            });
        });
    }

    // get_list_tokens() {
    //   return this.httpClient.get(this.server_nfluent+"/api/get_list");
    // }

    add_layer(l: any,w=0,h=0,preview=0) {
        const _l={...l}
        if(w>0 && h>0){
            _l.width=w;
            _l.height=h;
        }
        return this.httpClient.post(this.server_nfluent+"/api/layers/?preview="+preview,  _l);
    }



    get_url_collection(limit: number,
                       file_format:string,
                       ext="webp",
                       size="200,200",
                       seed=0,
                       quality=98,
                       target="preview",
                       data={},
                       attributes:any=[],
                       platform="nftstorage") {

        let url=this.server_nfluent+"/api/collection/?seed="+seed+"&image="+ext+"&name="+file_format+"&size=" + size+"&format="+target+"&limit="+limit+"&quality="+quality+"&platform="+platform;
        url=url+"&data="+btoa(encodeURIComponent(JSON.stringify(data)));
        url=url+"&attributes="+btoa(encodeURIComponent(JSON.stringify(attributes)));

        return url;

    }

    update_layer(l:Layer, limit=100) {
        return this.httpClient.post(this.server_nfluent+"/api/layers/?preview="+limit,l);
    }

    //recoit un objet aux propriétés filename & content
    upload(file: any ,platform:string="nftstorage",type="image/png",convert=""){
        if(platform!="nfluent"){
            return this.httpClient.post(this.server_nfluent+"/api/upload/?convert="+convert+"&platform="+platform+"&type="+type,file);
        }else{
            return this.httpClient.post(environment.server+"/api/upload/?convert="+convert+"&platform="+platform+"&type="+type,file);
        }
    }

    remove_image(name:string){
        return this.httpClient.delete(this.server_nfluent+"/api/images/"+encodeURI(name));
    }

    reset_collection() {
        return this._get("/reset_collection/");
    }

    save_config_on_server(body:Configuration,with_file=false,user="") {
        return this.httpClient.post(this.server_nfluent+"/api/configs/?with_file="+with_file+"&user="+user,body);
    }

    load_config(url:string,user:string="") {
        return this.httpClient.get<Configuration>(this.server_nfluent+"/api/configs/b64"+btoa(url)+"/?format=json&user="+user);
    }

    list_config() {
        return this._get("/configs/");
    }

    list_installed_fonts() {
        return this._get("/fonts/");
    }

    isValideToken(operation: string, query: string) {
        return this._get("/validate/","ope="+operation+"&q="+query);
    }

    send_confirmation(address: string,tokenid:string) {
        return this.httpClient.post(this.server_nfluent+"/api/send_conf",{address:address,tokenid:tokenid});
    }

    //nbr contient le nombre de nft a fournir
    get_new_token(ope: string,url_appli:string="",nbr=1) {
        if(url_appli=="")url_appli="https://tokenforge.nfluent.io";
        let url_api=this.server_nfluent+"/api/get_new_code/"+ope+"/"+btoa(url_appli)+"?limit="+nbr;
        return this.httpClient.get(url_api);
    }

    mint_for_contest(addr: string,ope:any,miner:string,metadata_storage:string,network:string,nft:NFT | null=null,nft_id=""){
        let body:any={
            account:addr,
            token: nft,
            nft_id:nft_id,
            network:network,
            miner:miner,
            ope:ope,
            metadata_storage:metadata_storage
        };

        body.type_network=this.network.indexOf("devnet")>-1 ? "devnet" : "mainnet";
        return this.httpClient.post(this.server_nfluent+"/api/mint_for_contest/",body);
    }


    get_operations(ope="",user="") {
        let url=this.server_nfluent+"/api/operations/?";
        if(ope.length>0)url=url+"ope="+encodeURIComponent(ope)
        if(user.length>0)url=url+"&user="+user;
        return this.httpClient.get<Operation>(url);
    }

    upload_operation(filename:string, content:any) {
        return this.httpClient.post(this.server_nfluent+"/api/operations/",{filename:filename,file:content});
    }

    delete_operation(ope: string) {
        return this.httpClient.delete(this.server_nfluent+"/api/operations/"+ope+"/");
    }

    get_nft_from_db(id: string) {
        return this._get("/get_nft_from_db/","id="+id);
    }

    validate(action:any, t:NFT,user_addr:string,operateur:string,operation_name:string) {
        let url=action.api.replace("$nfluent_server$",this.server_nfluent);
        $$("Appel de "+url+" suite a validation");
        return this.httpClient.post(url,{
            user:user_addr,
            operateur:operateur,
            operation:operation_name,
            network:t.network,
            token:t.address,
            attributes:t.attributes
        });
    }

    send_mail_to_validateur(operation: any,user:string) {
        return this.httpClient.post(this.server_nfluent+"/api/send_email_to_validateur/"+user,operation);
    }

    send_mail_to_contact(_from:string,message:string,subject="",name="") {
        let body={from:_from,message:message,subject:subject,name:name};
        return this.httpClient.post(this.server_nfluent+"/api/send_email_to_contact/",body);
    }

    send_transaction_confirmation(email: string, body: any) {
        return this.httpClient.post(this.server_nfluent+"/api/send_transaction_confirmation/"+email+"/",body)
    }

    clone_with_color(layer: any, origin_color: string, palette: string) {
        let body={
            layer:layer,
            color:origin_color,
            palette:palette
        }
        return this.httpClient.post(this.server_nfluent+"/api/clone_with_color/",body)
    }

    get_palettes() {
        return this._get("/palettes/");
    }

    getfaqs() {
        return this._get("/getyaml/faqs/","dir=./flaskr/static");
    }

    del_config(id_config:string,user:string="") {
        return this.httpClient.delete(this.server_nfluent+"/api/configs/"+id_config+"/");
    }

    apply_filter(layer_name: string, filter: string) {
        return this.httpClient.post(this.server_nfluent+"/api/apply_filter/",{layer:layer_name,filter:filter});
    }

    get_tokens_to_send(ope="",section="dispenser", limit=1000) {
        return this.httpClient.get(this.server_nfluent+"/api/get_tokens_to_send/"+encodeURIComponent(ope)+"/?limit="+limit+"&section="+section);
    }

    get_nfts_from_operation(ope:string){
        return this.httpClient.get<{nfts:NFT[],source:any}>(this.server_nfluent+"/api/nfts_from_operation/"+ope);
    }

    get_nfts_from_collection(collection_id:string,network:string){
        return this.httpClient.get<{nfts:NFT[]}>(this.server_nfluent+"/api/nfts_from_collection/"+collection_id+"/?network="+network);
    }

    transfer_to(mint_addr: string,
                to_addr: string,
                from_miner:CryptoKey,
                to_miner:CryptoKey,
                from_network:string,
                to_network:string,
                collection_id:string,
                mail_content="mail_new_account",
                operation_id="") {
        let body={
            token_id:mint_addr,
            dest:to_addr,
            from_miner:from_miner,
            from_network:from_network,
            to_network:to_network,
            target_miner: to_miner,
            collection_id: collection_id,
            mail_content:mail_content,
            operation:operation_id
        }
        return this.httpClient.post(
            this.server_nfluent+"/api/transfer/", body
        );
    }

    generate_svg(file_content:string,text_to_add:string,layer_name:string) {
        let data={
            file:file_content,
            sequence: text_to_add.split("|"),
            layer:layer_name,
            server:this.server_nfluent+"/api/images"
        }
        return this.httpClient.post(this.server_nfluent+"/api/generate_svg/",data);
    }

    create_account(network: string, email: string,new_account_mail="mail_new_account",existing_account_mail="mail_existing_account",dictionnary={}) {
        //On pourra utiliser %network% pour inserer le nom du réseau dans le nom des emails de confirmations
        let body={
            email:email,
            mail_new_wallet:new_account_mail.replace("%network%",network.split("-")[0]),
            mail_existing_wallet:existing_account_mail.replace("%network%",network.split("-")[0]),
            dictionnary:dictionnary
        }
        return this.httpClient.post(this.server_nfluent+"/api/keys/?network="+network,body);
    }


    export_to_prestashop(id:string,tokens:NFT[] | null=null,collection_filter=true) {
        if(!tokens || tokens?.length==0)
            return this.httpClient.get(this.server_nfluent+"/api/export_to_prestashop/?ope="+id+"&collection_filter="+collection_filter);
        else
            return this.httpClient.post(this.server_nfluent+"/api/export_to_prestashop/?ope="+id+"&collection_filter="+collection_filter,tokens);
    }


    qrcode(body:string,format:"image" | "json" | "qrcode"="image") {
        return this.httpClient.get<string>(this.server_nfluent+"/api/qrcode/?code="+body+"&format="+format);
    }

    get_access_code(addr: string) {
        return this.httpClient.get<string>(this.server_nfluent+"/api/access_code/"+addr+"?format=base64");
    }

    check_access_code(access_code: string) {
        return this.httpClient.get<string>(this.server_nfluent+"/api/check_access_code/"+access_code+"?format=base64");
    }

    get_nft(address: string, network: string,owner:string="") {
        return this.httpClient.get<any>(this.server_nfluent+"/api/nfts/"+address+"?network="+network+"&account="+owner);
    }

    add_user_for_nft(body:any) {
        return this.httpClient.post(this.server_nfluent+"/api/add_task_to_mintpool/",body);
    }

    is_beta() {
        return (this.version=="beta");
    }

    analyse_prestashop_orders(operation_id: string) {
        return this.httpClient.get(this.server_nfluent+"/api/analyse_prestashop_orders/?ope="+operation_id);
    }

    nftlive_access(addr: string, network: string="elrond-devnet") {
        return this.httpClient.get(this.server_nfluent+"/api/nftlive_access/"+addr+"/?network="+network);
    }

    send_photo_for_nftlive(limit:number,conf_id_or_url:string, dimensions:string,quality:number,note:string,dynamic_fields:any[], body: any,format="base64") {
        body["config"]=conf_id_or_url
        body["limit"]=limit
        body["dimensions"]=dimensions
        body["note"]=note;
        body["quality"]=quality
        body["dynamic_fields"]=dynamic_fields
        body["format"]=format
        return this._post("send_photo_for_nftlive/","",body,60000)
    }


    mint(token:NFT, miner:CryptoKey, owner:string,operation:string,sign=false,
         platform:string="nftstorage", network="",
         storage_file="",encrypt_nft=false) : Promise<any> {
        return new Promise((resolve, reject) => {
            let param="storage_file="+storage_file+"&keyfile="+miner.encrypt+"&owner="+owner+"&sign="+sign+"&platform="+platform+"&network="+network+"&operation="+operation
            param=param+"&encrypt_nft="+encrypt_nft;
            this.httpClient.post(this.server_nfluent+"/api/mint/?"+param,{nft:token,miner:miner}).subscribe((r)=>{
                resolve(r);
            },(err)=>{
                this.wait();
                reject(err);
            })
        });
    }


    save_privacy(addr: string, secret: string) {
        return this.httpClient.post(this.server_nfluent+"/api/save_privacy/",{addr:addr,secret:encrypt(secret)});
    }

    extract_zip(file:any) {
        return this.httpClient.post(this.server_nfluent+"/api/extract_zip/",file);
    }

    get_collections(owners_or_collections: string,network="",detail=false) {
        if(network.length==0)network=this.network;
        let url=this.server_nfluent+"/api/collections/"+owners_or_collections+"/?network="+network+"&detail="+detail+"&operations=canCreate";
        return this.httpClient.get<Collection[]>(url);
    }

    create_collection(new_collection: Collection) {
        return this.httpClient.post(this.server_nfluent+"/api/create_collection/?network="+this.network,new_collection);
    }

    get_minerpool() {
        return this.httpClient.get(this.server_nfluent+"/api/minerpool/");
    }

    run_mintpool(limit: number=3,filter="") {
        if(filter.length>0)filter="?filter="+filter
        return this.httpClient.get(this.server_nfluent+"/api/async_mint/"+limit+"/"+filter);
    }

    cancel_mintpool_treatment(id: string) {
        return this.httpClient.delete(this.server_nfluent+"/api/minerpool/"+id+"/");
    }

    edit_mintpool(ask_id:string,new_value:any) {
        return this.httpClient.post(this.server_nfluent+"/api/minerpool/"+ask_id+"/",new_value);
    }

    //Utilisé pour afficher la liste des validateurs
    get_validators() {
        return this.httpClient.get<Validator[]>(this.server_nfluent+"/api/validators/");
    }

    //Inscrit un nouveau validateur en avec la token
    subscribe_as_validator(ask_for="",network="",validator_name=""){
        return this.httpClient.post<any>(this.server_nfluent+"/api/validators/",{"validator_name":validator_name,"ask_for":ask_for,network:network});
    }

    set_operation_for_validator(validator_id: string, operation_id:string) {
        return this.httpClient.put(this.server_nfluent+"/api/validators/"+validator_id+"/",{operation:operation_id});
    }

    send_message_to_validator(validator_id: string, message:string) {
        return this.httpClient.post(this.server_nfluent+"/api/send_to_validator/"+validator_id+"/",{message:message});
    }

    scan_for_access(data:string,address:string) {
        return this.httpClient.post(this.server_nfluent+"/api/scan_for_access/",{validator:decodeURIComponent(data),address:address});
    }

    remove_validator(id:string) {
        return this.httpClient.delete(this.server_nfluent+"/api/validators/"+id+"/");
    }


    getyaml(filename:string) {
        if(filename.startsWith("http"))filename="b64:"+btoa(filename);
        return this.httpClient.get<any>(this.server_nfluent+"/api/getyaml/"+encodeURIComponent(filename)+"?format=json")
    }

    delete_ask(id: string) {
        return this.httpClient.delete(this.server_nfluent+"/api/minerpool/"+id+"/");
    }

    getExplorer(addr:string | undefined,_type="address") : string {
        if(this.isElrond())
            return "https://"+(this.isMain() ? "" : "devnet.")+"xspotlight.com/"+addr;
        if(this.isPolygon()){
            if(this.isMain()){
                return "https://polygonscan.com/"+_type+"/"+addr;
            }else{
                return "https://polygon.testnets-nftically.com/marketplace?search="+addr+"&chain[]=80001"
                //return "https://mumbai.polygonscan.com/"+_type+"/"+addr;
            }
        }
        return ""
    }

    open_explorer(addr: string,_type : "address" | "transactions" ="address") {
        let url=this.getExplorer(addr,_type)
        open(url,"explorer");
    }


    access_code_checking(access_code: string, address: string) {
        return this.httpClient.get(this.server_nfluent+"/api/access_code_checking/"+access_code+"/"+address+"/");
    }

    check_private_key(seed: string, address: string) {
        return this.httpClient.get(this.server_nfluent+"/api/check_private_key/"+seed+"/"+address+"/"+this.network);
    }

    getBalance(addr:string,network:string,token_id="") {
        let params="with_balance=true&network="+network;
        if(token_id.length>0)params=params+"&token_id="+token_id;
        return this._get("keys/"+addr+"/",params)
    }


    upload_attributes(config_name:string,file:string) {
        //Associer un fichier d'attributs au visuel des calques
        return this.httpClient.post(this.server_nfluent+"/api/upload_attributes_file/"+config_name+"/",file);
    }

    set_role(collection_id: string, owner: string, network: string) {
        return this.httpClient.post(this.server_nfluent+"/api/set_role_for_collection/",{
            network:network,
            collection_id:collection_id,
            owner:owner
        });
    }


    info_server() {
        return this._get("/infos/");
    }

    upload_batch(content:any) {
        return this.httpClient.post<NFT[]>(this.server_nfluent+"/api/upload_batch/",content);
    }

    upload_excel_file(content:any) {
        return this.httpClient.post<any[]>(this.server_nfluent+"/api/upload_excel/",content);
    }

    get_account(addr: string, network: string) {
        return this._get("accounts/"+addr,"network="+network);
    }

    rescue_wallet(email: string,database_server:string,network:string) {
        return this._get("rescue_wallet/"+email,"db="+database_server+"&network="+network);
    }

    isDevnet() {
        if(this.network.indexOf("devnet")>-1)return true;
        return false;
    }


    search_images(query: string,remove_background=false) {
        return this._get("search_images/","query="+query+"&remove_background="+remove_background);
    }

    remove_background(content: string) {
        return this.httpClient.post<any>(this.server_nfluent+"/api/remove_background/",content);
    }

    registration(email: string) {
        return this._get("registration/"+email+"/");
    }

    delete_account(access_code: string) {
        return this.httpClient.delete(this.server_nfluent+"/api/delete_account/"+access_code+"/")
    }

    update_access_code(access_code: string, new_password: string) {
        return this.httpClient.post(this.server_nfluent+"/api/update_password/"+access_code+"/",{access_code:new_password});
    }

    isFile() : boolean {
        return this.network.startsWith("file-");
    }

    check_network(router: Router) {
        if(!this.online)router.navigate(["pagenotfound"],{queryParams:{message:"Connexion au serveur impossible"}});
    }

    hashcode(doc: any[]) {
        return this._post("hashcode/","",{docs:doc});
    }

    isBlockchain() {
        return !(this.network.startsWith("db-") || this.network.startsWith("file-"))
    }

    get_sequence(layers: Layer[], limit: number,config:string="") {
        return this._post("get_sequence/","",{layers:layers,limit:limit,config:config});
    }


    get_composition(items:any[],layers:any[],data:any,size:string="500x500",format="webp",platform="server") {
        return this._post("get_composition/","",{format:format,size:size,data:data,items:items,layers:layers,platform:platform},200000);
    }

    create_zip(files:string[],email:string) {
        let body={
            email:email,
            files:files
        }
        return this._post("create_zip/","",body);
    }

    send_bill(dest: string,amount:string,
              subject: string="Votre facture",
              reference="",
              message="",
              description="",
              contact="support@nfluent.io",
              model="mail_facture.html") {
        let body={
            dest:dest,
            reference: reference,
            message: message,
            subject:subject,
            model:model,
            amount:amount,
            contact:contact,
            description:description
        }
        return this._post("send_bill/","",body,200000);
    }
}
