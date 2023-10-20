import {Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges} from '@angular/core';
import {$$, showError} from "../../tools";
import {Socket} from "ngx-socket-io";
import {Collection, Connexion} from "../../operation";
import {NetworkService} from "../network.service";
import {NFT} from "../../nft";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-autovalidator',
  templateUrl: './autovalidator.component.html',
  styleUrls: ['./autovalidator.component.css']
})
export class AutovalidatorComponent implements OnInit, OnDestroy, OnChanges {

  @Input() address: string = "";
  @Input() explain_message: string = "";
  @Input() title: any;
  @Input() network: string = "";
  @Input() validator_name: string = "";
  @Input() connexion: Connexion = {
    private_key: false,
    keystore: false,
    direct_connect: false,
    extension_wallet: false,
    web_wallet: false,
    address: false,
    email: false,
    google: false,
    nfluent_wallet_connect: false,
    on_device: false,
    wallet_connect: true,
    webcam: false
  }

  @Input() showCollections: boolean = true; //Vérifie si l'utilisateur dispose d'un ou plusieurs NFT

  @Output('validate') onvalidate: EventEmitter<string> = new EventEmitter();
  @Output('fail') onfail: EventEmitter<string> = new EventEmitter();

  @Input() collections: string[] = [];
  @Input() min_supply: number[] = [];
  _collections: Collection[] = [];
  validator: string = "";

  qrcode_enabled: boolean = true
  showNfluentWalletConnect: boolean = false;
  autorized_users:any={}
  show_authent: boolean = true;


  constructor(
      public socket: Socket,
      public api: NetworkService
  ) {
  }


  ngOnChanges(changes: SimpleChanges): void {
    if (this.showCollections && this.collections.length > 0) {
      if (typeof this.collections == "string") this.collections = [this.collections];

      this.api.get_collections(this.collections.join(","), this.network, true).subscribe((cols: Collection[]) => {
        $$("Récupération des collections", cols);
        this._collections = cols;
      })
    }

    if(this.collections.length>0){
      this.subscribe_as_validator();
    }
  }



  ngOnInit(): void {
    window.onbeforeunload = () => this.ngOnDestroy();
    this.socket.emptyConfig.url=environment.server
  }



  check_condition(nfts:NFT[]){
    $$("Vérification des conditions d'accès "+this.collections)
    for(let elts of this.collections) {
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

  subscribe_as_validator(){
    //Cette methode consiste à recevoir la liste des possésseurs de l'ensemble des tokens à valider
    if(this.validator_name.length==0)$$("Le système n'a pas de nom de validateur");
    if(this.collections.length==0)$$("Le système n'a pas de NFT à vérifier");

    if(this.collections.length>0 && this.validator_name.length>0){
      $$("Le systeme d'authent demande le QRCode en mode wallet_connect")

      if(typeof this.collections=="string")this.collections=[this.collections]; //Transforme le NFT en collection
      let cols=this.collections.join(",")
      $$("Demande d'enregistrement comme validateur pour les collections "+cols)
      this.api.subscribe_as_validator(cols,this.network,this.validator_name).subscribe((result:any)=>{
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
            if(data.message=="stop")this.show_authent=false;
          }
          // $$("Réception d'un message de la part du serveur",data);
          // let user_to_validate=data.address;
          // if(this.autorized_users.length==0 || this.autorized_users.indexOf(user_to_validate)>-1){
          //   $$("L'adresse reçue fait bien partie des adresses autorisés")
          //   this.onauthent.emit({address:user_to_validate,strong:true,nftchecked:true,provider:this.provider});
          // } else {
          //   $$("L'adresse reçue ne fait pas partie des adresses autorisés")
          //   this.oninvalid.emit({address:user_to_validate,strong:false,nftchecked:false});
          // }
        });
        // this.nfluent_wallet_connect_qrcode=this.api.server_nfluent+"/api/qrcode/"+encodeURIComponent(result.access_code);
        if(this.title=="" && this.showNfluentWalletConnect)this.title="Pointer ce QRcode avec votre 'NFluent Wallet'";
      },(err)=>{
        showError(this);
      })
    }
  }

  ngOnDestroy(): void {
    if(this.validator && this.validator.length>0){
      $$("Désenregistrement de "+this.validator);
      this.api.remove_validator(this.validator).subscribe(()=>{})
    }
  }


  check_nft(to_check: { strong: boolean; address: string; provider: any },min_supply=1) {
    if (to_check.strong) {
      if (this.autorized_users[to_check.address] >= min_supply) {
        this.onvalidate.emit(to_check.address);
      } else {
        $$("On rafraichie la liste des utilisateurs autorisé")
        this.api.subscribe_as_validator(this.collections.join(","), this.network, this.validator_name).subscribe((result: any) => {
              this.autorized_users = result.addresses;
              if (this.autorized_users[to_check.address] >= min_supply) {
                this.onvalidate.emit(to_check.address);
              } else {
                this.onfail.emit(to_check.address);
              }
            }
        )
      }
    }
  }
}
