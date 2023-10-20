import {AfterViewInit, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges} from '@angular/core';
import {NetworkService} from "../network.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {$$, showMessage} from "../../tools";

const BACKUP_IMG="https://tokenforge.nfluent.io/assets/icons/egld-token-logo.webp"

@Component({
  selector: 'app-token-selector',
  templateUrl: './token-selector.component.html',
  styleUrls: ['./token-selector.component.css']
})
export class TokenSelectorComponent implements OnChanges {
  @Input() network:string=""
  @Input() filter:string=""
  @Input() type:string="Fungible";
  @Input() size:string="30px";
  @Input() refresh_delay:number=0;
  @Input() owner:string=""
  @Input() show_createtoken_button=true;
  @Input("value") sel_token:any={id:""}
  @Input() label="Sélectionner un token"
  @Input() with_detail=false
  @Output() valueChange: EventEmitter<any> = new EventEmitter();
  @Output() endSearch: EventEmitter<any> = new EventEmitter();
  @Output() unselect: EventEmitter<any> = new EventEmitter();

  tokens:any[]=[]
  @Input() show_detail: boolean=true;
  message: string="";
  handler:any
  filter_by_name="";
  save_owner: string="";
  handle: any=0


  constructor(
      public api:NetworkService,
      public toast:MatSnackBar
  ) {

  }


  ngOnChanges(changes: SimpleChanges): void {
    if(changes["owner"] && changes["owner"].currentValue!="")this.save_owner=changes["owner"].currentValue
    if(changes["network"] || changes["filter"] || changes["owner"]){
      if(changes["owner"].currentValue==0)clearInterval(this.handle)
      this.refresh();
    }
    if(changes["refresh_delay"] && this.handle==0 && changes["refresh_delay"].currentValue>0){
      $$("Mise en place d'une collection des ESDT toute les "+changes["refresh_delay"].currentValue+" secondes")
      this.handle=setInterval(()=>{this.refresh()},changes["refresh_delay"].currentValue*1000)
    }
    if(!this.sel_token){
      this.sel_token={id:""}
    }
    if(typeof(this.sel_token)=="string"){
      this.sel_token={
        "id":this.sel_token,
        image:BACKUP_IMG,
        name:this.sel_token
      }
    }

  }


  refresh() : void {
    if(!this.filter)this.filter="";
    if(this.network=="")return

    if(!this.handle || this.refresh_delay==0)this.message="Recherche des monnaies"+(this.owner ? " de "+this.owner : "")
    this.api.find_tokens(this.network,this.owner,this.with_detail,2000).subscribe({next:(tokens:any[])=>{
        this.tokens=[];
        this.message=""
        for(let t of tokens){
          t["label"]=t["name"]
          if(t["balance"]>0)t["label"]=t["label"]+" ("+Math.round(t["balance"]*100)/100+")"
          this.tokens.push(t)
        }
        this.endSearch.emit(this.tokens);
      },error:()=>{this.message="";}
    })
  }

  update_sel($event: any) {
    this.sel_token=$event
    clearInterval(this.handle)
    this.handle=0
    if(this.sel_token.hasOwnProperty("value"))this.sel_token=this.sel_token.value;
    this.valueChange.emit(this.sel_token)
  }

  reset() {
    this.tokens=[]
    this.sel_token={id:""}
    this.refresh();
    this.unselect.emit(true)
  }


  update_filter() {
    clearTimeout(this.handler)
    this.handler=setTimeout(()=>{this.refresh()},1000)
  }

  switch_token() {
    if(this.owner==""){
      this.owner=this.save_owner;
      this.label="Monnaies du wallet"
    }else{
      this.label="Toutes les monnaies"
      this.owner=""
    }
    this.refresh();
  }

  open_create_esdt() {
    showMessage(this,"Depuis le wallet web, choisir la rubrique Create Token puis reporter l'identifiant",6000,()=>{
      open("https://wallet.multiversx.com/issue-token","wallet")
    },"Ouvrir le wallet")
  }
}
