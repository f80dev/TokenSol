import {Component, Input, OnInit} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-dbtable',
  templateUrl: './dbtable.component.html',
  styleUrls: ['./dbtable.component.css']
})
export class DbtableComponent implements OnInit {

  @Input("table") table:string="";
  @Input() source:any="local";
  @Input("max_len") max_len=20;
  @Input("excludes") excludes:string="";
  rows:any[]=[];
  cols:string[]=[];
  @Input() showClear=false;
  @Input() dictionnary:any={};

  constructor(
    public httpClient:HttpClient
  ) { }

  update_cols(cols:string[]){
    let rc=[];
    for(let c of cols){
      if(!this.dictionnary.hasOwnProperty(c))this.dictionnary[c]=c;
      rc.push(this.dictionnary[c]);
    }
    return rc;
  }

  update_cells(rows:any[]){
    for(let i=0;i<rows.length;i++){
      for(let k of Object.keys(rows[i])){
        let v=rows[i][k];
        if(typeof(v)=="boolean"){
          v=v ? "X" : "";
        }
        rows[i][this.dictionnary[k]]=v;
      }
    }
    return(rows);
  }



  refresh(){
    if(this.source=="db"){
      this.httpClient.get(environment.server+"/api/tables/"+this.table+"?excludes="+this.excludes).subscribe((rows:any)=>{
        this.rows=rows;
        if(this.cols.length==0){
          for(let k in this.rows[0]){
            this.cols.push(k);
          }
        }
      })
    } else {
      if(this.source){
        this.cols=this.update_cols(Object.keys(this.source[0]));
        this.rows=this.update_cells(this.source);
      }
    }

  }

  ngOnInit(): void {
    this.refresh()
  }

  clear() {
    if(this.source!="local"){
      this.httpClient.delete(environment.server+"/api/tables/"+this.table).subscribe(()=>{
        this.refresh();
      })
    }
  }

  truncate(txt:string) {
    if(txt && typeof txt=="string"){
      if(txt.length<this.max_len){
        return txt;
      } else {
        return txt.substring(0,this.max_len)+"...";
      }
    } else
      return txt;
  }
}
