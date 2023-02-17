import {Component,  OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {$$, detect_network, getParams, hasWebcam, isEmail, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {UserService} from "../user.service";
import {NFT} from "../../nft";
import {NFLUENT_WALLET} from "../../definitions";
import {Operation, Connexion, get_in} from "../../operation";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";
  wallet_link: string="";
  nft:NFT | null=null;
  final_message="";
  ope: Operation | null=null;
  webcam: boolean=true;
  authentification: Connexion | undefined;
  title: string="Envoyez ce NFT";
  prompt: string="Indiquer l'adresse ou l'email du destinataire";
  help_url: string="";
  section:string="dispenser";

  constructor(
    public routes:ActivatedRoute,
    public _location:Location,
    public userService:UserService,
    public network:NetworkService,
    public toast:MatSnackBar,
    public router:Router,
    public alias:AliasPipe
  ) { }


  ngOnInit(): void {
    hasWebcam(this.webcam);

    getParams(this.routes).then((params:any)=>{
      this.nft=params["token"];
      let ope=params["ope"];

      this.section=params["section"];
      if(!this.section)$$("!La section n'est pas renseignée");

      if(!this.nft){
        $$("On va chercher les NFTs dans le fichier d'opération");
        let address=params["address"] || "";
        let symbol=params["symbol"] || "";

        this.network.get_nfts_from_operation(ope).subscribe((r:any)=>{
          for(let nft of r["nfts"]){
            if((nft.address==address && address.length>0) || (nft.symbol==symbol && nft.address?.length==0))this.nft=nft;
          }
        });
      }

      this.selfWalletConnexion=params["selfWalletConnexion"] || (this.section=="lottery");

      if(ope){
        this.network.get_operations(ope).subscribe((result:any)=>{
          this.ope=result;
          this.prompt=get_in(this.ope,this.section+".messages.prompt",params.hasOwnProperty("prompt") ? params["prompt"] : "Indiquer l'adresse ou l'email du destinataire")
          if(this.ope){
            this.title=params.hasOwnProperty("title") ? params["title"] : get_in(this.ope,this.section+".messages.title","Distribution des NFTs")
            this.help_url=params.hasOwnProperty("help") ? params["help"] : get_in(this.ope,this.section+".messages.help","")
            this.authentification=get_in(this.ope,this.section+".authentification",{showEmail:true})
          }
        })
      }

    })
  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";
  hasWebcam=true;
  billing_address="";
  selfWalletConnexion: boolean=false;

  lost(){
    $$("Lost")
    if(this.ope && this.ope.lottery && this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.looser.message,this.ope.lottery.end_process.looser.redirection)
    } else {
      this.end_process("Ce NFT vous a échapé");
    }
  }

  win(){
    $$("Win")
    if(this.ope && this.ope.lottery && this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.winner.message,this.ope.lottery.end_process.winner.redirection)
    } else {
      this.end_process("Ce NFT est le votre.");
    }
  }

  end_process(sMessage:string,rediction:string | null=null){
    if(rediction){
      showMessage(this,sMessage);
      setTimeout(()=>{
        if(this.ope && this.ope.lottery) open(this.ope!.lottery.end_process.winner.redirection);
        },3500);
    } else {
      this.message=sMessage+". Vous pouvez fermer cette écran";
    }
  }

  valide(evt: { address:string }) {
    let addr=evt.address;
    this.address=addr.replace("'","");
    addr=this.alias.transform(addr,"address");
    if(this.nft && (this.nft!.address?.startsWith("db_") || this.nft!.address?.startsWith("file_"))){
      $$("Ce token est issue d'une base de données, donc non miné");
      if(this.ope){
        if(!this.ope.lazy_mining){
          $$("Section lazy_mining manquante")
          return;
        }
        

        let miner:string=this.nft.miner;
        let network:string=detect_network(miner)+(this.ope.network.indexOf("devnet") ? "-devnet" : "-mainnet");
        if(isEmail(this.address)){
            if(miner.length==0)miner=this.ope.lazy_mining.networks[0].miner;
            if(network?.length==0)network=this.ope.lazy_mining.networks[0].network;
        } else {
          //TODO: faire le test en mettant comme destinataire une adresse polygon et elrond
          for(let n of this.ope.lazy_mining.networks){
            if(n.network.split("-")[0]==detect_network(this.address) && network.length==0 && miner.length==0){
                network=n.network;
                miner=n.miner;                
            }
          }
        }

        
        this.message=get_in(this.ope,this.section+".messages.confirm","Votre NFT est en cours de préparation");

        this.network.mint(this.nft,miner,this.address,this.ope.id,true,"",network).then((r:any)=>{
          this.message="";
          if(r.error.length>0){
            this.message=r.error+". ";
          } else {
            this.win();
          }
        },(err:any)=>{
          showError(this,err);
          this.message="";
        })
      }
    }else{
      let mint_addr=this.nft!.address;
      if(mint_addr!=""){
        $$("Ce token est déjà miné, on se contente de le transférer");
        this.message=get_in(this.ope,this.section+".messages.confirm","Votre NFT est en cours de préparation");
        this.network.transfer_to(mint_addr!,addr,this.nft!.owner!,this.network.network,this.ope?.new_account.mail).subscribe((r:any)=>{
          this.message="";
          this.wallet_link=NFLUENT_WALLET+"?"+r.nfluent_wallet;
          if(this.selfWalletConnexion){
            this.final_message="Retrouver votre nouveau NFT dans votre wallet NFluenT";
          } else {
            this.final_message="Le NFT est livré à l'adresse "+addr;
          }
        },(err:any)=>{
          showMessage(this,get_in(this.ope,this.section+".messages.cancel","Problème technique: Impossible d'envoyer ce NFT"));
          this.final_message="Problème technique: Envoi du NFT annulé";
        })
      }
    }
  }

  onLoadPaymentData($event: any) {
    if($event.returnValue)
      this.valide({address:this.address});
  }

  onflash($event: any) {
    this.address=$event.data;
  }

  cancel() {
    this.final_message="Annulation. Vous pouvez fermer cette fenêtre";
  }

  validate_input_address() {
    if(!isEmail(this.address) && !this.network.isElrond(this.address)){
      showMessage(this,"Le service n'est compatible qu'avec les adresses elrond ou les adresses mails");
    } else {
      this.valide({address:this.address});
    }
  }

  open_help() {
    open(this.help_url,"Aide");
  }
}
