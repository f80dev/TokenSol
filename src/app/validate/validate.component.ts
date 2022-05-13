import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  operation: string ="calvi2022";
  query: string="";

  constructor(public routes:ActivatedRoute,public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.operation=this.routes.snapshot.queryParamMap.get("operation") || "calvi2022";
  }

  search(query:string){
    this.network.isValideToken("calvi2022",query).subscribe((r:any)=>{

    })
  }

  update_model() {
    if(this.query.length>5)
      this.search(this.query);
  }
}
