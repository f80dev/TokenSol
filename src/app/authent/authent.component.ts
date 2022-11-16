//Version 0.1

import {WalletProvider} from "@elrondnetwork/erdjs-web-wallet-provider";
import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {$$, isLocal, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {WalletConnectProvider} from "@elrondnetwork/erdjs-wallet-connect-provider/out";
import {environment} from "../../environments/environment";
import {Location} from "@angular/common";
import {ActivatedRoute} from "@angular/router";
import {WALLET_PROVIDER_DEVNET, WALLET_PROVIDER_MAINNET} from "@elrondnetwork/erdjs-web-wallet-provider/out/constants";
import {NFT} from "../../nft";
import {GoogleLoginProvider, SocialAuthService} from "@abacritt/angularx-social-login";
import {Collection, Operation} from "../../operation";
import {Socket} from "ngx-socket-io";

@Component({
  selector: 'app-authent',
  templateUrl: './authent.component.html',
  styleUrls: ['./authent.component.css']
})
export class AuthentComponent implements OnInit,OnDestroy {

  @Input() intro_message:string="Email / Adresse de blockchaine";
  @Input() network:string="elrond-devnet";
  @Input() operation:string="";
  @Input() validator_name:string="";
  @Input() checknft:string[]=[]; //Vérifie si l'utilisateur dispose d'un ou plusieurs NFT
  @Input() showCollections:boolean=true; //Vérifie si l'utilisateur dispose d'un ou plusieurs NFT
  @Input() explain_message:string="Adresse de votre wallet ou votre email si vous n'en avez pas encore";
  @Input() autoconnect_for_localhost=false;   //Connection automatique sur le localhost
  @Input() prompt="Votre email / Adresse dans la blockchain";   //Connection automatique sur le localhost

  @Output('authent') onauthent: EventEmitter<{strong:boolean,nftchecked:boolean,address:string}>=new EventEmitter();
  @Output('invalid') oninvalid: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();
  @Output('disconnect') onlogout: EventEmitter<any>=new EventEmitter();


  @Input() showAccesCode=false;         //Code secret d'accès (réservé)
  @Input() showCancel=false;         //Code secret d'accès (réservé)
  @Input() showWebcam=false;            //utilisation du QRCode dynamique du wallet nFluent
  @Input() showDynamicToken=false;      //Code dynamique utilisable en copié collé (a priori pas d'usage)
  @Input() showGoogle=false;            //Authentification via Google (pour les personnes souhaitant laissé un mail)
  @Input() showWalletConnect=false;
  @Input() showAddress=false;
  @Input() showNetwork=false;
  @Input() showEmail=false;             //Code d'accès envoyé par email
  @Input() showNfluentWalletConnect=false;
  @Input() address: string="";

  strong=false;                     //Niveau d'authentification
  @Input() size="350px";
  @Input() title=""

  qrcode: string="";
  access_code="";

  collections: Collection[]=[];
  nfluent_wallet_connect_qrcode="";
  autorized_users:string[]=[];        //Liste de l'ensemble des utilisateurs autorisé
  validator: string="";
  provider: WalletConnectProvider;
  _operation: Operation | undefined;


  constructor(
    public api:NetworkService,
    public _location:Location,
    public routes:ActivatedRoute,
    public socket:Socket,
    public socialAuthService: SocialAuthService,
    public toast:MatSnackBar
  ) {

    this.provider=new WalletConnectProvider(
      "https://bridge.walletconnect.org",
      {
        onClientLogin: ()=> {
          if(this.provider){
            $$("Login");
            this.provider.getAddress().then((addr:string)=>{
              this.address=addr;
              this.validate();
              this.strong=true;
              if(this.provider){
                this.provider.getSignature().then((sign:string)=>{
                  $$("signature="+sign);
                })
              }

            })
          }
        },
        onClientLogout: ()=> {
          $$("Déconnection");
          this.strong=false;
          this.onlogout.emit();
        },
      }
    );
  }


  ngOnDestroy(): void {
    $$("Desenregistrement de "+this.validator);
        this.api.remove_validator(this.validator).subscribe(()=>{})
    }



  subscribe_as_validator(){
    $$("Le systeme d'authent demande le QRCode en mode wallet_connect")
    this.api.subscribe_as_validator(this.checknft.join(","),this.network,this.validator_name).subscribe((result:any)=>{
      //On inscrit le systeme à la reception de message
      this.validator=result.id;
      $$("Le validator est enregistré sour "+this.validator)
      this.autorized_users=result.addresses;
      this.socket.on(result.id,(data:any) => {
        $$("Réception d'un message de la part du serveur",data);
        let user_to_validate=data.address;
        if(this.autorized_users.length==0 || this.autorized_users.indexOf(user_to_validate)>-1){
          this.onauthent.emit({address:user_to_validate,strong:true,nftchecked:true});
        } else {
          this.oninvalid.emit();
        }
      });
      this.nfluent_wallet_connect_qrcode=environment.server+"/api/qrcode/"+encodeURIComponent(result.access_code);
      if(this.title=="" && this.showNfluentWalletConnect)this.title="Pointer ce QRcode avec votre 'NFluent Wallet'";
    },(err)=>{
      showError(this);
    })
  }



  refresh(){
    $$("Refresh de l'écran");
    if(this.title=="" && this.showWalletConnect)this.title="Pointer ce QRcode avec un wallet compatible 'Wallet Connect'";

    if (this.provider) {
      if (this.showCollections && this.checknft && this.checknft.length > 0) {
        this.api.get_collections(this.checknft.join(","),this.network,true).subscribe((cols: Collection[]) => {
          $$("Récupération des collections", cols);
          this.collections = cols;
        })
      }

      this.provider.init().then((b: boolean) => {
        if (this.provider) {
          this.provider.login().then((s: string) => {
            this.qrcode = environment.server + "/api/qrcode/" + encodeURIComponent(s);
          });
        }
      });

      if (isLocal(environment.appli) && this.showAccesCode && this.autoconnect_for_localhost) {
        this.onauthent.emit({address: "erd16ck62egnvmushkfkut3yltux30cvp5aluy69u8p5hezkx89a2enqf8plt8",nftchecked:false,strong:true});
      }
    }

    if(this.showGoogle){
      this.socialAuthService.authState.subscribe((socialUser) => {
        this.strong=true;
        this.onauthent.emit({
          address: socialUser.email,
          nftchecked:false,strong:true});
      },(err)=>{
        $$("Erreur de connexion",err);
      });
    }

    this.subscribe_as_validator();
  }



  ngOnInit(): void {
    window.onbeforeunload = () => this.ngOnDestroy();

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
        this.checknft=ope.validate?.filters.collections || [];
        this.network=ope.network;
        this.refresh();
        }
      )
    } else this.refresh();
  }


  open_wallet() {
    if(this.network.indexOf("elrond")>-1) {
      let callback_url=environment.appli + this._location.path().split("?")[0];
      let url_wallet=this.network.indexOf("devnet")==-1 ? WALLET_PROVIDER_MAINNET : WALLET_PROVIDER_DEVNET;
      new WalletProvider(url_wallet).login({
        callbackUrl:callback_url
      }).then((result) => {
        this.address = result;
        this.strong = true;
        this.onauthent.emit({address:this.address,strong:true,nftchecked:false});
      })
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
    this.onauthent.emit({address:this.address,nftchecked:true,strong:this.strong})
    if(this._operation && this._operation.validate?.actions.success && this._operation.validate?.actions.success.redirect.length>0)
      open(this._operation.validate?.actions.success.redirect);
  }


  validate() {
    if(this.address && this.address.indexOf("@")==-1 && !this.api.isElrond(this.address)){
      showMessage(this,"Pour l'instant, Le service n'est compatible qu'avec les adresses elrond");
    } else {
      if(this.checknft.length>0){
        $$("Recherche des tokens "+this.checknft+" pour l'adresse "+this.address);
        this.api.get_tokens_from("owner",this.address,1000,true,null,0,this.network).then((r:NFT[])=>{
          if(this.check_condition(r)){
            this.success();
          } else {
            this.onauthent.emit({address:this.address,nftchecked:false,strong:this.strong})
          }
        })
      } else {
        this.success();
      }
    }
  }


  update_address() {

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
      if(this.access_code.length==8){
        this.api.access_code_checking(this.access_code,this.address).subscribe(()=>{
          this.strong_connect();
        },(err:any)=>{
          showMessage(this,'Code incorrect');
        })
      }
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
}
