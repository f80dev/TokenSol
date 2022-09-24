import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {getParams} from "../../tools";

@Component({
  selector: 'app-page-not-found',
  templateUrl: './page-not-found.component.html',
  styleUrls: ['./page-not-found.component.css']
})
export class PageNotFoundComponent implements OnInit {
  message: string="Veuillez réessayer";

  constructor(
    public routes:ActivatedRoute
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("message"))this.message=params["message"];
    })
  }

}
