import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  constructor(public routes:ActivatedRoute,public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.network.get_nfts_balance_from_ftx().subscribe((r:any)=>{
      debugger
    })
  }

}
