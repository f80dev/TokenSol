import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {getParams, removeBigInt, showError, showMessage} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NFT} from "../nfts/nfts.component";
import {Observable, Subject} from "rxjs";
import {WalletConnectProvider} from '@elrondnetwork/erdjs-wallet-connect-provider';
import {WalletProvider} from "@elrondnetwork/erdjs-web-wallet-provider"
import {Location} from "@angular/common";

//Test : http://localhost:4200/wallet?addr=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr&toolbar=false
@Component({
  selector: 'app-mywallet',
  templateUrl: './mywallet.component.html',
  styleUrls: ['./mywallet.component.css']
})
export class MywalletComponent implements OnInit,OnDestroy {
  nfts: NFT[]=[];
  indexTab: number=0;
  addr:any="";
  url_key: any="";
  showDetail=false;
  takePhoto=false;

  @Input("filter") filter="";

  private trigger: Subject<void> = new Subject<void>();
  private nextWebcam: Subject<boolean|string> = new Subject<boolean|string>();
  photo_to_send: string="";
  qrcode:string="";
  qrcode_addr:string="";
  provider:any=null;
  private hAccessCode: any;
  access_code: any;

  constructor(public user:UserService,
              public routes:ActivatedRoute,
              public toast:MatSnackBar,
              public _location:Location,
              public network:NetworkService) {
    this.provider=new WalletConnectProvider(
      "https://bridge.walletconnect.org/",
      {
        onClientLogin: ()=> {
          debugger
          alert('Logged in')
        },
        onClientLogout: ()=> {
          alert('Logged out')
        }
      }
    );
  }


  generate_qrcode(){
    this.network.get_access_code(this.addr).subscribe((r:any)=>{
        this.url_key=r.image;
        this.access_code=r.access_code;
      });
  }

  ngOnInit(): void {
    this.provider.init().then((b:boolean)=>{
      this.provider.login().then((s:string)=>{
        this.qrcode=environment.server+"/api/qrcode/?code="+s;
      });
    });

    getParams(this.routes).then((params:any)=>{
      this.addr=params["addr"];
      if(!this.addr)showMessage(this,"Adresse non disponible, vous pouvez fermer cette fenêtre");
      this.showDetail=params["show_detail"] || false;
      this.network.network=params["network"] || "elrond-devnet";
      this.generate_qrcode();
      this.hAccessCode=setInterval(()=>{this.generate_qrcode()},30000);
      this.takePhoto=params["takePhoto"];
      this.refresh();
    });
  }

  open_elrond_authent() {
    //voir : https://docs.elrond.com/wallet/webhooks/#:~:text=The%20web%20wallet%20webhooks%20allow,form%20with%20the%20provided%20arguments.
    let callback=environment.appli+this._location.path();
    new WalletProvider(this.network.url_wallet()).login({callbackUrl:callback,redirectDelayMilliseconds:2000}).then((result)=>{

    })
  }

  refresh(index:number=0) {
    if(index==0 && this.nfts.length==0){
      this.network.wait("Chargement de vos NFTs");
      for(let arg of [[0,20],[21,50],[51,100],[101,200]]){
        let offset=arg[0];
        let limit=arg[1];
        setTimeout(()=>{
          this.network.get_tokens_from("owner",this.addr,limit,false,null,offset,this.network.network).then((r:NFT[])=>{
            for(let nft of r){
              this.nfts.push(nft);
            }
            if(r.length==0) {
              if (arg[0] == 0)
                showMessage(this, "Vous n'avez aucun NFT pour l'instant")
              else
                this.network.wait("");
            }
          }).catch(err=>{showError(this,err)});
        },offset*500);
      }
    }
  }

  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }

  public get nextWebcamObservable(): Observable<boolean|string> {
    return this.nextWebcam.asObservable();
  }


  handleImage(event: any) {
    var rc=event.imageData;
    this.photo_to_send="data:image/jpeg;base64,"+btoa(rc["data"])
  }


  photo() {
    this.trigger.next();
  }

  send() {
    this.photo_to_send="";
  }

  ngOnDestroy(): void {
    clearInterval(this.hAccessCode);
  }

  show_elrond_addr() {
    this.network.qrcode(this.addr,"json").subscribe((result:any)=>{
      this.qrcode_addr=result.qrcode;
    })

  }

  get_nft(nft: NFT) {
    if(nft.owner && nft.address){
      this.network.get_nft(nft.owner,nft.address,this.network.network).subscribe(()=>{
        debugger
      });
    }
  }
}
