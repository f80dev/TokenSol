import {Component, Input, OnInit} from '@angular/core';
import {environment} from "../../environments/environment";
import {Router} from "@angular/router";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-signature',
  templateUrl: './signature.component.html',
  styleUrls: ['./signature.component.css']
})
export class SignatureComponent implements OnInit {

  @Input() faq="";
  appname="";
  version="";
  @Input() color="white";

  constructor(
    public router:Router,
    public network:NetworkService,
  ) { }

  ngOnInit(): void {
    this.appname=environment.appname;
    this.version=environment.version;
  }

  open_faq() {
    this.router.navigate(["faqs"],{queryParams:{open:this.faq}});
  }

  open_mail(){
    open("mailto:"+environment.mail);
  }

  open_forum(){
    open(environment.forum);
  }
}
