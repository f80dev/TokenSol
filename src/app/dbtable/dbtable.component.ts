import {Component, Input, OnInit} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {environment} from "../../environments/environment";
import {showMessage} from "../../tools";

@Component({
  selector: 'app-dbtable',
  templateUrl: './dbtable.component.html',
  styleUrls: ['./dbtable.component.css']
})
export class DbtableComponent implements OnInit {

  @Input("table") table:string="";
  @Input("max_len") max_len=20;
  @Input("excludes") excludes:string="";
  rows:any[]=[];
  cols: string[]=[];

  constructor(
    public httpClient:HttpClient
  ) { }

  refresh(){
    this.httpClient.get(environment.server+"/api/tables/"+this.table+"?excludes="+this.excludes).subscribe((rows:any)=>{
      this.rows=rows;
      if(this.cols.length==0){
        for(let k in this.rows[0]){
          this.cols.push(k);
        }
      }
    })
  }

  ngOnInit(): void {
    this.refresh()
  }

  clear() {
    this.httpClient.delete(environment.server+"/api/tables/"+this.table).subscribe(()=>{
      this.refresh();
    })
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
