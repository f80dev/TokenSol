//Version 0.1
import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {$$, isEmail, isLocal, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {environment} from "../../environments/environment";
import {Location} from "@angular/common";
import {ActivatedRoute} from "@angular/router";
import {NFT} from "../../nft";
import {SocialAuthService} from "@abacritt/angularx-social-login";
import {Collection, get_in, Operation} from "../../operation";
import {Socket} from "ngx-socket-io";
import {ADDR_ADMIN} from "../../definitions";
import {DeviceService} from "../device.service";
import { WalletConnectV2Provider } from "@multiversx/sdk-wallet-connect-provider";
import { ExtensionProvider } from "@multiversx/sdk-extension-provider";
import {WALLET_PROVIDER_DEVNET, WALLET_PROVIDER_MAINNET, WalletProvider} from "@multiversx/sdk-web-wallet-provider/out";

//Installation de @multiversx/sdk-wallet-connect-provider via yarn add @multiversx/sdk-wallet-connect-provider

@Component({
  selector: 'app-authent',
  templateUrl: './authent.component.html',
  styleUrls: ['./authent.component.css']
})
export class AuthentComponent implements OnInit,OnDestroy {

  @Input() intro_message:string="";
  @Input() network:string="elrond-devnet";
  @Input() operation:string="";
  @Input() validator_name:string="";
  @Input() paiement:{address:string, amount:number,description:string} | undefined;
  @Input() checknft:string[]=[]; //Vérifie si l'utilisateur dispose d'un ou plusieurs NFT
  @Input() showCollections:boolean=true; //Vérifie si l'utilisateur dispose d'un ou plusieurs NFT
  @Input() explain_message:string="Adresse de votre wallet ou votre email si vous n'en avez pas encore";
  @Input() autoconnect_for_localhost=false;   //Connection automatique sur le localhost
  @Input() prompt="Votre email / Adresse dans la blockchain";   //Connection automatique sur le localhost

  @Output('authent') onauthent: EventEmitter<{strong:boolean,nftchecked:boolean,address:string,provider:any}>=new EventEmitter();
  @Output('invalid') oninvalid: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();
  @Output('disconnect') onlogout: EventEmitter<any>=new EventEmitter();
  //@Output('init_wallet') init_wallet: EventEmitter<{ provider:any,address:string }>=new EventEmitter();


  @Input() showAccesCode=false;         //Code secret d'accès (réservé)
  @Input() showCancel=false;         //Code secret d'accès (réservé)
  @Input() showWebcam=false;            //utilisation du QRCode dynamique du wallet nFluent
  @Input() showDynamicToken=false;      //Code dynamique utilisable en copié collé (a priori pas d'usage)
  @Input() use_cookie: boolean = false;
  @Input() showGoogle=false;            //Authentification via Google (pour les personnes souhaitant laissé un mail)
  @Input() showWalletConnect=false;
  @Input() showWebWallet=false;
  @Input() showExtensionWallet=false;
  @Input() walletConnect_ProjectId="ea9073e2f07f3d98fea76d4f26f789fe"
  @Input() showAddress=false;
  @Input() showNetwork=false;
  @Input() showPrivateKey=false;
  @Input() showEmail=false;             //Code d'accès envoyé par email
  @Input() showNfluentWalletConnect=false;
  @Input() address: string="";
  @Input() nfluent_server: string=environment.server;

  @Input() directShowQRCode:boolean=false;      //Propose directement les qrcodes ou laisse l'utilisateur le demander (par défaut)

  strong=false;                     //Niveau d'authentification
  @Input() size="350px";
  @Input() title=""

  qrcode: string="";
  access_code="";

  collections: Collection[]=[];
  nfluent_wallet_connect_qrcode="";
  autorized_users:string[]=[];        //Liste de l'ensemble des utilisateurs autorisé
  validator: string="";
  provider: any
  _operation: Operation | undefined;
  private_key="";
  enabled_webcam: boolean=false;
  qrcode_enabled: boolean=true;

  relayUrl:string = "wss://relay.walletconnect.com";
  result_nft_check: boolean=true;


  constructor(
    public api:NetworkService,
    public _location:Location,
    public routes:ActivatedRoute,
    public socket:Socket,
    public device:DeviceService,
    public socialAuthService: SocialAuthService,
    public toast:MatSnackBar
  ) {

    const callbacks:any ={
        onClientLogin: async ()=> {
              this.address=await this.provider.getAddress();
              },
        onClientLogout: ()=> {},
      }

    this.provider = new WalletConnectV2Provider(callbacks, this.get_chain_id(), this.relayUrl, this.walletConnect_ProjectId);

  }

  async init_wallet_provider(){
    await this.provider.init();
  }

  private toHex(stringToConvert: string) {
    return stringToConvert
        .split('')
        .map((c) => c.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('');
  }


  ngOnDestroy(): void {
    $$("Désenregistrement de "+this.validator);
    this.api.remove_validator(this.validator).subscribe(()=>{})
  }


  subscribe_as_validator(){
    if(this.validator_name.length==0)$$("Le système n'a pas de nom de validateur");
    if(this.checknft.length==0)$$("Le système n'a pas de NFT à vérifier");

    if(this.checknft.length>0 && this.validator_name.length>0){
      $$("Le systeme d'authent demande le QRCode en mode wallet_connect")

      if(typeof this.checknft=="string")this.checknft=[this.checknft];
      this.api.subscribe_as_validator(this.checknft.join(","),this.network,this.validator_name).subscribe((result:any)=>{
        //On inscrit le systeme à la reception de message
        this.validator=result.id;
        $$("Le validator est enregistré sour "+this.validator)
        this.autorized_users=result.addresses;

        this.socket.on("connect",(() => {
          this.qrcode_enabled=true;
          $$("Le validateur est connecté");
        }))
        this.socket.on("disconnect",(() => {
          this.qrcode_enabled=false;
          $$("Le validateur est déconnecté");
        }))

        $$("Le validateur s'inscrit à la réception des événements "+result.id)
        this.socket.on(result.id,(data:any) => {
          if(data.hasOwnProperty("message")){
            if(data.message=="stop")this.showNfluentWalletConnect=false;
          }
          $$("Réception d'un message de la part du serveur",data);
          let user_to_validate=data.address;
          if(this.autorized_users.length==0 || this.autorized_users.indexOf(user_to_validate)>-1){
            $$("L'adresse reçue fait bien partie des adresses autorisés")
            this.onauthent.emit({address:user_to_validate,strong:true,nftchecked:true,provider:this.provider});
          } else {
            $$("L'adresse reçue ne fait pas partie des adresses autorisés")
            this.oninvalid.emit({address:user_to_validate,strong:false,nftchecked:false});
          }
        });
        this.nfluent_wallet_connect_qrcode=this.api.server_nfluent+"/api/qrcode/"+encodeURIComponent(result.access_code);
        if(this.title=="" && this.showNfluentWalletConnect)this.title="Pointer ce QRcode avec votre 'NFluent Wallet'";
      },(err)=>{
        showError(this);
      })
    }
  }


  refresh(){
    $$("Refresh de l'écran");
    if(this.title=="" && this.showWalletConnect)this.title="Pointer ce QRcode avec un wallet compatible 'Wallet Connect'";

    if (this.provider) {
      if (this.showCollections && this.checknft && this.checknft.length > 0) {
        if(typeof this.checknft=="string")this.checknft=[this.checknft];
        this.api.get_collections(this.checknft.join(","),this.network,true).subscribe((cols: Collection[]) => {
          $$("Récupération des collections", cols);
          this.collections = cols;
        })
      }

      this.init_wallet_provider();

      // this.provider.init().then((b: boolean) => {
      //   if (this.provider) {
      //     this.provider.login().then((s: string) => {
      //       this.qrcode = this.api.server_nfluent + "/api/qrcode/" + encodeURIComponent(s);
      //     });
      //   }
      // });

      if (isLocal(environment.appli) && this.showAccesCode && this.autoconnect_for_localhost) {
        this.onauthent.emit({address: ADDR_ADMIN,nftchecked:false,provider:this.provider,strong:true});
      }
    }

    if(this.showGoogle){
      this.socialAuthService.authState.subscribe((socialUser) => {
        this.strong=true;
        this.onauthent.emit({
          address: socialUser.email,
          provider:this.provider,
          nftchecked:false,strong:true});
      },(err)=>{
        $$("Erreur de connexion",err);
      });
    }

    this.subscribe_as_validator();
  }



  ngOnInit(): void {
    window.onbeforeunload = () => this.ngOnDestroy();

    this.api.server_nfluent=this.nfluent_server;
    this.socket.emptyConfig.url=this.nfluent_server;
    this.address="";
    if(this.use_cookie)this.address=localStorage.getItem("authent_address") || "";
    this.device.isHandset$.subscribe((r:boolean)=>{
      if(r){
        this.showExtensionWallet=false;
      }
    });

    if(this.operation.length>0){
      $$("On utilise "+this.operation+" pour le paramétrage du module");
      this.api.get_operations(this.operation).subscribe((ope)=> {
        this._operation=ope;
        this.showGoogle = ope.validate?.authentification.google || false;
        this.showWebcam = ope.validate?.authentification.webcam || false;
        this.showAddress = ope.validate?.authentification.address || false;
        this.showNfluentWalletConnect = ope.validate?.authentification.nfluent_wallet_connect || false;
        this.showWalletConnect=ope.validate?.authentification.wallet_connect || false;
        this.showEmail = ope.validate?.authentification.email || false;
        this.checknft=get_in(ope,"validate.filters.collections",get_in(ope,"validate.collections",[]))
        if(this.checknft.length==0){
          //Recherche de collection dans les sources
          for(let src of ope.data.sources){
            this.checknft=get_in(src,"collection",get_in(src,"filter.collection",[]))
            if(this.checknft.length>0)break
          }
          if(this.checknft.length==0){
            //Recherche de collection dans le lazy_mining
            for(let network of get_in(ope,"lazy_mining.networks",[])){
              this.checknft=get_in(network,"collection",[])
              if(this.checknft.length>0)break;
            }
          }
        }
        this.network=ope.network;
        this.refresh();
        }
      )
    } else this.refresh();
  }


  open_wallet() {
    if(this.network.indexOf("elrond")>-1) {
      let callback_url=environment.appli + this._location.path().split("?")[0];
      // let url_wallet=this.network.indexOf("devnet")==-1 ? WALLET_PROVIDER_MAINNET : WALLET_PROVIDER_DEVNET;
      // new WalletProvider(url_wallet).login({
      //   callbackUrl:callback_url
      // }).then((result) => {
      //   this.address = result;
      //   this.strong = true;
      //   this.onauthent.emit({address:this.address,strong:true,nftchecked:false});
      // })
    }
  }


  check_condition(nfts:NFT[]){
    $$("Vérification des conditions d'accès "+this.checknft)
    for(let elts of this.checknft) {
      for (let elt of elts.split(" & ")) {
        for (let nft of nfts) {
          if(nft.collection && nft.collection.id == elt)return true;
          if(elt == nft.address)return true;
          //if (nft.collection && nft.collection.name) elt = elt.replace(nft.collection.name, "")
        }
        //if (elt.length == 0) return true;
      }
    }
    return false;
  }


  success(){
    //Se charge de retourner le message d'authentification réussi
    this.onauthent.emit({address:this.address,nftchecked:this.result_nft_check,provider:this.provider,strong:this.strong})
    if(this._operation && this._operation.validate?.actions.success && this._operation.validate?.actions.success.redirect.length>0)
      open(this._operation.validate?.actions.success.redirect);
  }


  validate(address="") {
    if(address.length>0){
      this.address=address;
      if(this.use_cookie)localStorage.setItem("authent_address",address);
    }

    if(!isEmail(this.address) && !this.api.isElrond(this.address)){
      showMessage(this,"Pour l'instant, Le service n'est compatible qu'avec les adresses mail ou elrond");
    } else {
      if(this.checknft.length>0){
        $$("Recherche des tokens "+this.checknft+" pour l'adresse "+this.address);
        this.api.get_tokens_from("owner",this.address,1000,true,null,0,this.network).then((r:any)=>{
          this.result_nft_check=this.check_condition(r.result);
          this.success();
        })
      } else {
        this.result_nft_check=true; //Forcément vrai puisqu'il n'y a aucun NFT a posséder
        this.success();
      }
    }
  }


  update_address(new_addr:string) {
    this.address=new_addr;
  }


  connect(network: string) {
    if(network=="elrond"){
      // @ts-ignore
      open(this.network.url_wallet(),"walletElrond")
    }

    if(network=="solana"){
      // @ts-ignore
      if(window.solflare || window.phantom){
        // this.solWalletS.connect().then( (wallet:Wallet) => {
        //   this.user.init(wallet).then((profil:any)=>{
        //     // if(requis.length>0){
        //     //   if(profil.perms.indexOf("*")==-1 && profil.perms.indexOf(requis)==-1)
        //     //     this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
        //     // }
        //     //
        //   });
        // }).catch((err:any) => {
        //   console.log("Error connecting wallet", err );
        //   this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
        // })
      }
    }

    // if(network=="google"){
    //   let servicePlatform = GoogleLoginProvider.PROVIDER_ID;
    //   this.socialAuthService.signIn(servicePlatform).then((socialUser:any) => {
    //     this.user.email=socialUser.email;
    //     this.user.name=socialUser.firstName + " "+ socialUser.lastName;
    //     this.strong=true;
    //   },(err:any)=>{
    //     $$("Erreur de connexion via google ",err);
    //     showMessage(this,"Problème d'authentification, veuillez saisir manuellement votre email");
    //   })
    // }

    if(network=="code"){
      if(this.access_code && this.access_code.length==8){
        this.api.access_code_checking(this.access_code,this.address).subscribe(()=>{
          this.strong_connect();
        },(err:any)=>{
          showMessage(this,'Code incorrect');
        })
      }
    }

    if(network=="private_key" && this.access_code.split(" ").length>=12){
      this.api.check_private_key(this.private_key,this.address).subscribe(()=>{
        this.strong_connect();
      },()=>{
        showMessage(this,'Phrase incorrecte');
      })
    }
  }


  on_flash($event: {data:string}) {
    $$("Lecture de l'adresse "+$event.data);
    if($event.data.length>20){
      this.api.check_access_code($event.data).subscribe((result:any)=>{
        this.address=result.addr;
        this.validate();
      },(err:any)=>{
        showMessage(this,"Code incorrect")
      })
    }
  }

  private strong_connect() {
    this.strong=true;
    showMessage(this,"Authentification validée.")
    this.validate()
  }

  update_dynamic_token() {
    navigator.clipboard.readText().then(
      text => {
        this.on_flash({data:text});
      }
    )
      .catch(error => {
          showMessage(this,'Impossible de lire le presse-papier');
        }
      );

  }

  cancel_webcam() {
    showMessage(this,"Impossible de démarrer la webcam");
    this.showWebcam=false;
  }

  get_chain_id(){
    return this.network.indexOf("devnet") ? "D" : "T"
  }


  async open_extension_wallet() {
      //https://docs.multiversx.com/sdk-and-tools/sdk-js/sdk-js-signing-providers/#the-extension-provider-multiversx-defi-wallet
      this.provider=ExtensionProvider.getInstance();
      let rc=await this.provider.init();
      let address=await this.provider.login();
      this.strong=true;
      this.validate(address);

      //this.init_wallet.emit({provider:this.provider,address:this.address});
  }

  async open_web_wallet(){
    //https://docs.multiversx.com/sdk-and-tools/sdk-js/sdk-js-signing-providers/#the-web-wallet-provider
    this.provider=new WalletProvider(this.network.indexOf("devnet")>-1 ? WALLET_PROVIDER_DEVNET : WALLET_PROVIDER_MAINNET)
    try{
      const url = encodeURIComponent(environment.appli);
      let rc=await this.provider.login({callbackUrl:url})
      this.strong=true;
      this.validate(this.provider.account.address);

      //this.init_wallet.emit({provider:this.provider,address:this.address});
      $$("Connexion web wallet ok "+rc)

    } catch (e) {
      this.strong=false;
    }
  }

  async open_wallet_connect() {
    //https://docs.multiversx.com/sdk-and-tools/sdk-js/sdk-js-signing-providers/#the-wallet-connect-provider
    const { uri, approval } = await this.provider.connect();
    this.qrcode=this.api.server_nfluent+"/api/qrcode/"+encodeURIComponent(uri);
    let address=await this.provider.login({approval});
    if(address){
      //this.init_wallet.emit({provider:this.provider,address:this.address});
      this.strong=true;
      this.validate(address);
    } else {
      this.oncancel.emit();
    }
  }


}
