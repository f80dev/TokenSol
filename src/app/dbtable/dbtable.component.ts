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
}
