import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";

@Component({
  selector: 'app-contest',
  templateUrl: './contest.component.html',
  styleUrls: ['./contest.component.css']
})
export class ContestComponent implements OnInit {

  ope:string | null="";
  qrcode: string="";

  constructor(
    public routes:ActivatedRoute,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.ope=this.routes.snapshot.queryParamMap.get("ope");
    setInterval(()=>{
      this.network.contest_status(this.ope).subscribe((r:any)=>{
        this.qrcode=r.qrcode;
      })
    })
  }

}
