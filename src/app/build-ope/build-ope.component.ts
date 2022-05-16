import { Component, OnInit } from '@angular/core';
import {MatSelectChange} from "@angular/material/select";
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-build-ope',
  templateUrl: './build-ope.component.html',
  styleUrls: ['./build-ope.component.css']
})
export class BuildOpeComponent implements OnInit {
  selected_ope: any={};
  url: string="";
  opes: any[]=[];

  constructor(
    public network:NetworkService,
  ) { }

  ngOnInit(): void {
    this.network.get_operations().subscribe((r:any)=>{
      this.opes=r;
    })
  }

  refresh($event: MatSelectChange) {
    this.url=environment.appli+"/contest?ope="+$event.value.code;
  }
}
