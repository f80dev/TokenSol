import {Router} from "@angular/router";
import {Component, OnInit} from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Observable } from 'rxjs';
import { map, shareReplay } from 'rxjs/operators';
import {UserService} from "./user.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'NFTCalvi';

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  constructor(
    private breakpointObserver: BreakpointObserver,
    public user:UserService,
    public router:Router
  ) {}

  ngOnInit(): void {
    this.user.disconnect();
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
}
