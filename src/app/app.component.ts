import {ActivatedRoute, Router} from "@angular/router";
import { Component, OnInit} from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import {UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {NETWORKS} from "../definitions";
import {MetabossService} from "./metaboss.service";
import {getParams} from "../tools";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = environment.appname;
  version=environment.version;

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  networks=NETWORKS;
  toolbar_visible: string="true";


  constructor(
    private breakpointObserver: BreakpointObserver,
    public user:UserService,
    public network_service:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public metaboss:MetabossService
  ) {}

  ngOnInit(): void {
    this.user.disconnect();
    setTimeout(()=>{
      this.toolbar_visible=getParams(this.routes,"toolbar","true");
      this.update_network();
    },500);
  }

  logout(){
    this.user.disconnect();
    this.router.navigate(["about"]);
  }


  login() {
    this.user.connect().then((addr)=>{
      this.router.navigate(["wallet"]);
    })
  }


  update_network() {
      this.metaboss.init_keys(this.network_service.network);
  }
}
