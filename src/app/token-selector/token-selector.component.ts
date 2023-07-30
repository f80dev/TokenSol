import {AfterViewInit, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges} from '@angular/core';
import {NetworkService} from "../network.service";

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
  @Input() owner:string=""
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



  constructor(
      public api:NetworkService
  ) {

  }


  ngOnChanges(changes: SimpleChanges): void {
    if(changes["network"] || changes["filter"] || changes["owner"]){
      //wait_message(this,"Recherche des monnaies")
      setTimeout(()=>{this.refresh();},1000);
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
    this.message="Recherche des monnaies"+(this.owner ? " de "+this.owner : "")
    this.api.find_tokens(this.network,this.owner,this.with_detail,500).subscribe({next:(tokens:any[])=>{
        this.tokens=[];
        this.message=""
        for(let t of tokens){
          t["label"]=t["name"]
          if(t["balance"]!="")t["label"]=t["label"]+" ("+t["balance"]+")"
          this.tokens.push(t)
        }
        this.endSearch.emit(this.tokens);
      },error:()=>{this.message="";}
    })
  }

  update_sel($event: any) {
    this.sel_token=$event
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
}
