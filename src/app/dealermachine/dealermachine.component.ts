import {Component,  OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {$$, getParams, hasWebcam, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {UserService} from "../user.service";
import {NFT} from "../../nft";
import {NFLUENT_WALLET} from "../../definitions";
import {Operation,Connexion} from "../../operation";

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
  mining: any={};
  authentification: Connexion | undefined;
  title: string="Envoyez ce NFT";
  prompt: string="Indiquer l'adresse ou l'email du destinataire";

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
      let section=params["section"];
      if(params.hasOwnProperty("title"))this.title=params["title"]
      if(params.hasOwnProperty("prompt"))this.prompt=params["prompt"]

      if(!section)$$("!La section n'est pas renseignée");

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

      this.mining=params["mining"];
      this.selfWalletConnexion=params["selfWalletConnexion"] || (section=="lottery");

      if(ope){
        this.network.get_operations(ope).subscribe((ope:any)=>{
          this.ope=ope;
          if(this.ope){
            // @ts-ignore
            if(section && this.ope[section]){
              // @ts-ignore
              this.authentification=this.ope[section].authentification;
            }
            this.mining=params["mining"] || this.ope.lazy_mining;
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
    addr=this.alias.transform(addr,"pubkey");
    if(this.nft!.address?.startsWith("db_") || this.nft!.address?.startsWith("file_")){
      $$("Ce token est issue d'une base de données, donc non miné");
      if(this.ope){
        this.message=this.ope.store!.support.buy_message;
        this.network.mint_for_contest(addr,this.ope.id,this.mining.miner,this.mining.metadata_storage,this.ope.network,this.nft!).subscribe((r:any)=>{
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
        this.message="Envoi du NFT en cours sur "+addr;
        this.network.transfer_to(mint_addr!,addr,this.nft!.owner!,this.network.network,this.ope?.new_account.mail).subscribe((r:any)=>{
          this.message="";
          this.wallet_link=NFLUENT_WALLET+"?"+r.nfluent_wallet;
          if(this.selfWalletConnexion){
            this.final_message="Retrouver votre nouveau NFT dans votre wallet NFluenT";
          } else {
            this.final_message="Le NFT est livré à l'adresse "+addr;
          }

        },(err:any)=>{
          showMessage(this,"Impossible d'envoyer ce NFT");
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
    if(this.address && this.address.indexOf("@")==-1 && !this.address.startsWith('\'') && !this.network.isElrond(this.address)){
      showMessage(this,"Le service n'est compatible qu'avec les adresses elrond");
    } else {
      this.valide({address:this.address});
    }
  }
}
