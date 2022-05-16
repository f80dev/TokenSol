import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-contest',
  templateUrl: './contest.component.html',
  styleUrls: ['./contest.component.css']
})
//test: http://127.0.0.1:4200/contest?ope=calvi2022
export class ContestComponent implements OnInit {

  ope:string | null="";
  qrcode: string="";
  url: string="";
  visual: string="";

  constructor(
    public routes:ActivatedRoute,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.ope=this.routes.snapshot.queryParamMap.get("ope");

    setInterval(()=>{
      this.network.get_new_token(this.ope!,environment.appli).subscribe((r:any)=>{
        this.qrcode=r.qrcode;
        this.url=r.url;
        this.visual=r.visual || "";
      })
    },3000);
  }

}
