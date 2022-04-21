import {ActivatedRoute, Router} from "@angular/router";
import {AfterViewInit, Component, OnInit} from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import {UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {NETWORKS} from "../definitions";
import {MetabossService} from "./metaboss.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = environment.appname;

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  networks=NETWORKS;

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
      this.network_service.network=this.routes.snapshot.queryParamMap.get("network") || "devnet";
    },500);
  }

  logout(){
    this.user.disconnect();
    this.router.navigate(["about"]);
  }


  login() {
    this.user.connect(()=>{
      this.router.navigate(["wallet"]);
    })
  }

  refresh() {
  }


    update_network() {
        this.metaboss.keys(this.network_service.network).subscribe((keys)=>{this.network_service.keys=keys;});
    }
}
