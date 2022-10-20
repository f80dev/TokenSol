import { Injectable } from '@angular/core';
import {
  clusterApiUrl,
  Connection,
  LAMPORTS_PER_SOL,
  PublicKey,
  RpcResponseAndContext, SignatureResult,
  TransactionSignature
} from "@solana/web3.js";
import {TOKEN_PROGRAM_ID} from "@solana/spl-token";
import * as SPLToken from "@solana/spl-token";
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {$$, encrypt, words} from "../tools";
import {environment} from "../environments/environment";

import {retry, Subject, timeout} from "rxjs";
import {Collection, Operation} from "../operation";
import {NFT, SolanaToken, SplTokenInfo, Validator} from "../nft";
import {Layer} from "../create";



@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private _network:string="elrond-devnet";
  private _connection: Connection=new Connection(clusterApiUrl("devnet"), 'confirmed');
  waiting: string="";
  complement: string | undefined ="";
  fiat_unity: string="$";
  version: string="0.1";
  network_change=new Subject<string>();

  constructor(
    private httpClient : HttpClient
  ) {

  }



  get_tokens(pubkey: PublicKey,f:Function) {
    return new Promise((resolve, reject) => {
      f(pubkey, {programId: TOKEN_PROGRAM_ID})
        .then((r:any) => {
          let rc = [];
          for (let t of r.value) {
            rc.push(t);
          }
          resolve(rc);
        }).catch((err:Error)=>{reject(err)});
    });
  };



  get network(): string {
    return this._network;
  }

  set network(value: string) {
    this._network = value;
    if(this._network){
      // @ts-ignore
      let network_name=(value=="solana-devnet") ? "devnet" : "mainnet-beta";
      // @ts-ignore
      this._connection=new Connection(clusterApiUrl(network_name), 'confirmed');
      this.network_change.next(value);
    }

  }

  get connection(): Connection {
    return this._connection;
  }

  set connection(value: Connection) {
    this._connection = value;
  }

  getBalance(publicKey: PublicKey) : Promise<number> {
    return new Promise((resolve, reject) => {
      this.connection.getBalance(publicKey).then(r => {resolve(r/1000000000);});
    });
  }

  airdrop(publicKey: PublicKey) : Promise<RpcResponseAndContext<SignatureResult>> {
    this.waiting="Airdrop en cours";

    return this.connection.requestAirdrop(publicKey, LAMPORTS_PER_SOL).then(
      (airdropSignature: TransactionSignature) => {
        this.waiting="";
        return this.connection.confirmTransaction(airdropSignature);
      }
    );


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

  unity_conversion: any={};


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

        splTokenInfo["pubkey"] = e.pubkey;
        let layoutInfo = SPLToken.MintLayout.decode(e.account.data);
        let mintAuthority=layoutInfo.mintAuthority.toBase58();
        splTokenInfo.amount=Number(splTokenInfo.amount);

        if(filter==null || (filter.mintAuthority && mintAuthority==filter.mintAuthority)){
          $$("Analyse de "+mintAddress);
          this.httpClient.get(environment.server+"/api/scan/"+mintAddress+"?network="+this.network).subscribe((token_account:any)=>{
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


  // all_nfts() : Promise<any[]> {
  //   return new Promise((resolve,reject) => {
  //     new TokenListProvider().resolve().then((tokens:any) => {
  //       const tokenList = tokens.filterByClusterSlug(this._network).getList();
  //       resolve(tokenList);
  //     }).catch((err:any) => {
  //       reject(err);
  //     });
  //   });
  // }
  //
  //
  // build_token_from_ftx(t:any) : SolanaToken {
  //   let l_attributes=t.attributesList;
  //   l_attributes.push({trait_type:"redeemable",value:t.redeemable});
  //   l_attributes.push({trait_type:"redeemed",value:t.redeemed});
  //   let token:SolanaToken={
  //     splMintInfo: undefined,
  //     splTokenInfo: undefined,
  //     mint:t.solMintAddress,
  //     network:this.network,
  //     address:t.solMintAddress,
  //     metadataPDA:{},
  //     metadataOffchain: {
  //       seller_fee_basis_points: t.royaltyFeeRate*100,
  //       issuer:t.issuer,
  //       attributes:l_attributes,
  //       collection: t.collection,
  //       name: t.name,
  //       description: t.description,
  //       image: t.imageUrl,
  //       external_url: "",
  //       properties: {
  //         files:[
  //           {uri:t.imageUrl,type:""},{uri:t.animationUrl,type:""}
  //         ],
  //         caterogy:"",
  //         creators:[]
  //       },
  //     },
  //     metadataOnchain:{
  //       type:"nft",
  //       updateAuthority:"",
  //       mint:t.solMintAddress,
  //       key:t.id,
  //       data:{
  //         symbol:"",
  //         name:t.name,
  //         uri:"",
  //         sellerFeeBasisPoints:t.royaltyFeeRate*100,
  //         creators:[]
  //       },
  //       isMutable:0,
  //       primarySaleHappened:0
  //     },
  //     search:{collection:t.collection,metadata:""}
  //   }
  //   return token;
  // }
  //

  get_tokens_from(type_addr:string,addr:string,limit=100,short=false,filter:any=null,offset=0,network="elrond-devnet") : Promise<any[]> {

    $$("Recherche de token par "+type_addr)
    return new Promise((resolve,reject) => {
      if(addr==null){
        reject();
      } else {
        if(this.network.indexOf("solana")>-1){
          let func:any=null;

          // if(type_addr=="FTX_account"){
          //   this.get_tokens_from_ftx(addr).then((tokens:any)=>{
          //     let rc:SolanaToken[]=[];
          //     for(let t of tokens){
          //       let token:SolanaToken=this.build_token_from_ftx(t);
          //       if(tokens.length<10){
          //         this.solscan_info(t.solMintAddress).then((dt:any)=>{
          //           token.metadataOnchain=dt.data.metadata
          //           rc.push(token);
          //           resolve(rc);
          //         })
          //       } else {
          //         rc.push(token);
          //       }
          //     }
          //     if(tokens.length>10)resolve(rc);
          //   });
          // }

          if(type_addr=="owner"){
            this.httpClient.get(environment.server+"/api/nfts/?with_attr="+(!short)+"&limit="+limit+"&offset="+offset+"&account="+addr+"&network="+this.network).subscribe((r:any)=>{
              resolve(r);
            })

            // this.connection.getTokenAccountsByOwner(new PublicKey(addr),{programId: TOKEN_PROGRAM_ID},"confirmed").then((result:any)=> {
            //   let values=result.value;
            //   $$(values.length+" nfts trouvés");
            //   values=values.slice(offset,limit);
            //   if(values.length==0)resolve(values);
            //
            //   let completed_token=0;
            //   for(let k=0;k<values.length;k++){
            //     this.complete_token(addr,values[k],filter,short).then(token => {
            //       completed_token++;
            //       values[k]=token;
            //       if(completed_token==values.length){
            //         resolve(values);
            //       }
            //     }).catch((err)=>{
            //       $$("Anomalie, tous les NFTs ne sont pas analysé");
            //       resolve(values);
            //     })
            //
            //   }
            //
            // }).catch((err:any)=>{reject(err);});
          }

          if(type_addr=="token"){
            this.build_token_from_solscan(addr).then((token:SolanaToken)=>{
              resolve([token]);
            }).catch((err)=>{
              reject(err);
            });
            return;
          }

        }

        if(this.network.indexOf("elrond")>-1){
          this.httpClient.get(environment.server+"/api/nfts/?limit="+limit+"&offset="+offset+"&account="+addr+"&network="+this.network).subscribe((r:any)=>{
            resolve(r);
          },(err:any)=>{
            reject(err);
          })
        }



        if(type_addr=="miner"){
          //TODO function en chantier
          this.httpClient.get(environment.server+"/api/token_by_delegate/?account="+addr+"&network="+this.network).subscribe((r:any)=> {
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
    if(addr.length==0){
      return this.network.indexOf("elrond")>-1;
    } else {
      return addr.startsWith("erd");
    }


  }

  isSolana(network="") {
    if(network=="")network=this.network;
    return network.indexOf("solana")>-1;
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
      let url=environment.server+"/api/ftx/tokens/";
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

  get_list_tokens() {
    return this.httpClient.get(environment.server+"/api/get_list");
  }

  add_layer(l: any,w=0,h=0,preview=0) {
    const _l={...l}
    if(w>0 && h>0){
      _l.width=w;
      _l.height=h;
    }
    return this.httpClient.post(environment.server+"/api/layers/?preview="+preview,  _l);
  }

  get_collection(limit: number,file_format:string,ext="webp",size="200,200",seed=0,quality=98,target="preview",data={},attributes:any=[],platform="nftstorage") {
    let url=environment.server+"/api/collection/?seed="+seed+"&image="+ext+"&name="+file_format+"&size=" + size+"&format="+target+"&limit="+limit+"&quality="+quality+"&platform="+platform;

    url=url+"&data="+btoa(encodeURIComponent(JSON.stringify(data)));
    url=url+"&attributes="+btoa(encodeURIComponent(JSON.stringify(attributes)));

    return this.httpClient.get(
      url,
      { headers: new HttpHeaders({ timeout: `${200000}` }) }
    );
  }

  update_layer(l:Layer, limit=100) {
    return this.httpClient.post(environment.server+"/api/layers/?preview="+limit,l);
  }

  //recoit un objet aux propriétés filename & content
  upload(file: any ,platform="nftstorage",type="image/png",convert=""){
    if(platform!="nfluent"){
      return this.httpClient.post(environment.server+"/api/upload/?convert="+convert+"&platform="+platform+"&type="+type,file);
    }else{
      return this.httpClient.post("https://server.f80lab.com:4242/api/upload/?convert="+convert+"&platform="+platform+"&type="+type,file);
    }
  }

  remove_image(name:string){
    return this.httpClient.delete(environment.server+"/api/images/"+encodeURI(name));
  }

  reset_collection() {
    return this.httpClient.get(environment.server+"/api/reset_collection/");
  }

  save_config_on_server(name:string,body:any,with_file=false) {
    return this.httpClient.post(environment.server+"/api/configs/"+encodeURIComponent(name)+"/?with_file="+with_file,{filename:name,file:body});
  }

  load_config(name:string) {
    return this.httpClient.get(environment.server+"/api/configs/"+encodeURI(name)+"/?format=json");
  }

  list_config() {
    return this.httpClient.get(environment.server+"/api/configs/");
  }

  list_installed_fonts() {
    return this.httpClient.get(environment.server+"/api/fonts/");
  }

  isValideToken(operation: string, query: string) {
    return this.httpClient.get(environment.server+"/api/validate/?ope="+operation+"&q="+query);
  }

  send_confirmation(address: string,tokenid:string) {
    return this.httpClient.post(environment.server+"/api/send_conf",{address:address,tokenid:tokenid});
  }

  //nbr contient le nombre de nft a fournir
  get_new_token(ope: string,url_appli:string="",nbr=1) {
    if(url_appli=="")url_appli="https://tokenfactory.nfluent.io";
    let url_api=environment.server+"/api/get_new_code/"+ope+"/"+btoa(url_appli)+"?limit="+nbr;
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
    return this.httpClient.post(environment.server+"/api/mint_for_contest/",body);
  }


  get_operations(ope="") {
    return this.httpClient.get<Operation>(environment.server+"/api/operations/"+ope);
  }

  upload_operation(filename:string, content:any) {
    return this.httpClient.post(environment.server+"/api/operations/",{filename:filename,file:content});
  }

  delete_operation(ope: string) {
    return this.httpClient.delete(environment.server+"/api/operations/"+ope+"/");
  }

  get_nft_from_db(id: string) {
    return this.httpClient.get(environment.server+"/api/get_nft_from_db/?id="+id);
  }

  validate(action:any, t:NFT,user_addr:string,operateur:string,operation_name:string) {
    let url=action.api.replace("$nfluent_server$",environment.server);
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
    return this.httpClient.post(environment.server+"/api/send_email_to_validateur/"+user,operation);
  }

  send_transaction_confirmation(email: string, body: any) {
    return this.httpClient.post(environment.server+"/api/send_transaction_confirmation/"+email+"/",body)
  }

  clone_with_color(layer: any, origin_color: string, palette: string) {
    let body={
      layer:layer,
      color:origin_color,
      palette:palette
    }
    return this.httpClient.post(environment.server+"/api/clone_with_color/",body)
  }

  get_palettes() {
    return this.httpClient.get(environment.server+"/api/palettes/");
  }

  getfaqs() {
    return this.httpClient.get(environment.server+"/api/getyaml/faqs");
  }

  del_config(id_config:string) {
    return this.httpClient.delete(environment.server+"/api/configs/"+id_config+"/");
  }

  apply_filter(layer_name: string, filter: string) {
    return this.httpClient.post(environment.server+"/api/apply_filter/",{layer:layer_name,filter:filter});
  }

  get_tokens_to_send(ope="",section="dispenser", limit=1000) {
    return this.httpClient.get(environment.server+"/api/get_tokens_to_send/"+ope+"/?limit="+limit+"&section="+section);
  }

  get_nfts_from_operation(ope:string){
    return this.httpClient.get<NFT[]>(environment.server+"/api/nfts_from_operation/"+ope);
  }

  transfer_to(mint_addr: string, to_addr: string,owner:string,network="") {
    if(network.length==0)network=this.network;
    return this.httpClient.get(environment.server+"/api/transfer_to/"+encodeURIComponent(mint_addr)+"/"+encodeURIComponent(to_addr)+"/"+encodeURIComponent(owner)+"/?network="+network);
  }

  generate_svg(file_content:string,text_to_add:string,layer_name:string) {
    let data={
      file:file_content,
      sequence: text_to_add.split("|"),
      layer:layer_name,
      server:environment.server+"/api/images"
    }
    return this.httpClient.post(environment.server+"/api/generate_svg/",data);
  }

  // create_account(network: string, alias: string) {
  //   return this.httpClient.get(environment.server+"/api/create_account/"+network+"/"+alias+"/");
  // }
  export_to_prestashop(id:string,tokens:NFT[] | null=null,collection_filter=true) {
    if(!tokens || tokens?.length==0)
      return this.httpClient.get(environment.server+"/api/export_to_prestashop/?ope="+id+"&collection_filter="+collection_filter);
    else
      return this.httpClient.post(environment.server+"/api/export_to_prestashop/?ope="+id+"&collection_filter="+collection_filter,tokens);
  }


  qrcode(body:string,format:"image" | "json" | "qrcode"="image") {
    return this.httpClient.get<string>(environment.server+"/api/qrcode/?code="+body+"&format="+format);
  }

  get_access_code(addr: string) {
    return this.httpClient.get<string>(environment.server+"/api/access_code/"+addr+"?format=base64");
  }

  check_access_code(access_code: string) {
    return this.httpClient.get<string>(environment.server+"/api/check_access_code/"+access_code+"?format=base64");
  }

  get_nft(address: string, network: string) {
    return this.httpClient.get<any>(environment.server+"/api/nfts/"+address+"?network="+network);
  }

  add_user_for_nft(body:any) {
    return this.httpClient.post(environment.server+"/api/add_user_for_nft/",body);
  }

  is_beta() {
    return (this.version=="beta");
  }

  analyse_prestashop_orders(operation_id: string) {
    return this.httpClient.get(environment.server+"/api/analyse_prestashop_orders/?ope="+operation_id);
  }

  nftlive_access(addr: string, network: string="elrond-devnet") {
    return this.httpClient.get(environment.server+"/api/nftlive_access/"+addr+"/?network="+network);
  }

  send_photo_for_nftlive(limit:number,conf_id:string, dimensions:string,quality:number,note:string,dynamic_fields:any[], body: any) {
    body["limit"]=limit
    body["dimensions"]=dimensions
    body["note"]=note;
    body["quality"]=quality
    body["dynamic_fields"]=dynamic_fields
    return this.httpClient.post(environment.server+"/api/send_photo_for_nftlive/"+conf_id+"/",body)
  }


  mint(token:NFT, miner:string, owner:string,sign=false, platform="nftstorage", network="",storage_file=""){
    return new Promise((resolve, reject) => {
      this.wait("Minage en cours sur "+network);
      this.httpClient.post(environment.server+"/api/mint/?storage_file="+storage_file+"&keyfile="+miner+"&owner="+owner+"&sign="+sign+"&platform="+platform+"&network="+network,token).subscribe((r)=>{
        this.wait();
        resolve(r);
      },(err)=>{
        this.wait();
        reject(err);
      })
    });
  }

  save_privacy(addr: string, secret: string) {
    return this.httpClient.post(environment.server+"/api/save_privacy/",{addr:addr,secret:encrypt(secret)});
  }

  extract_zip(file:any) {
    return this.httpClient.post(environment.server+"/api/extract_zip/",file);
  }

  get_collections(owners_or_collections: string,network="",detail=false) {
    if(network.length==0)network=this.network;
    return this.httpClient.get<Collection[]>(environment.server+"/api/collections/"+owners_or_collections+"/?network="+network+"&detail="+detail);
  }

  create_collection(owner: string, new_collection: Collection) {
    return this.httpClient.post(environment.server+"/api/create_collection/"+owner+"/?network="+this.network,new_collection);
  }

  get_minerpool() {
    return this.httpClient.get(environment.server+"/api/minerpool/");
  }

  run_mintpool(limit: number=3,filter="") {
    if(filter.length>0)filter="?filter="+filter
    return this.httpClient.get(environment.server+"/api/async_mint/"+limit+"/"+filter);
  }

  cancel_mintpool_treatment(id: string) {
    return this.httpClient.delete(environment.server+"/api/minerpool/"+id+"/");
  }

  edit_mintpool(ask_id:string,new_value:any) {
    return this.httpClient.post(environment.server+"/api/minerpool/"+ask_id+"/",new_value);
  }

  //Utilisé pour afficher la liste des validateurs
  get_validators() {
    return this.httpClient.get<Validator[]>(environment.server+"/api/validators/");
  }

  subscribe_as_validator(ask_for="",network=""){
    return this.httpClient.post<any>(environment.server+"/api/validators/",{"ask_for":ask_for,network:network});
  }

  set_operation_for_validator(validator_id: string, operation_id:string) {
    return this.httpClient.put(environment.server+"/api/validators/"+validator_id+"/",{operation:operation_id});
  }

  scan_for_access(data:string,address:string) {
    return this.httpClient.post(environment.server+"/api/scan_for_access/",{validator:decodeURIComponent(data),address:address});
  }

  _get(url: string, param: string) {
    return this.httpClient.get<any>(url+"?"+param)
  }

  remove_validator(id:string) {
    return this.httpClient.delete(environment.server+"/api/validators/"+id+"/");
  }


  getyaml(filename:string) {
    return this.httpClient.get<string>(environment.server+"/api/getyaml/"+filename)
  }

  delete_ask(id: string) {
    return this.httpClient.delete(environment.server+"/api/minerpool/"+id+"/");
  }

  open_gallery(id: string | undefined) {
    let url="";
    if(this.isElrond() && id){
      let suffixe="/"+id;
      if(id.split("-").length==3){
        suffixe="/nfts/"+id;
      }else {
        if (!id.startsWith("erd")) suffixe = "/collections/" + id;
      }
      url="https://"+(this.isMain() ? "" : "devnet.")+"inspire.art"+suffixe;
    }

    open(url,"gallery")
  }

  access_code_checking(access_code: string, address: string) {
    return this.httpClient.get(environment.server+"/api/access_code_checking/"+access_code+"/"+address+"/");
  }

  upload_attributes(config_name:string,file:string) {
    //Associer un fichier d'attributs au visuel des calques
    return this.httpClient.post(environment.server+"/api/upload_attributes_file/"+config_name+"/",file);
  }
}
