import {Injectable} from '@angular/core';
import {Platform} from "@angular/cdk/platform";
import {Observable} from "rxjs";
import {BreakpointObserver, Breakpoints} from "@angular/cdk/layout";
import {map, shareReplay} from "rxjs/operators";
import {Title} from "@angular/platform-browser";


@Injectable({
  providedIn: 'root'
})
export class DeviceService {

  modele:any
  width: number=window.innerWidth;
  large=true;
  isHandset$: Observable<boolean>;
  smallScreen:Observable<boolean>;

  constructor(
      breakpointObserver: BreakpointObserver,
      platform:Platform,
      private titleService:Title
  ) {
    this.modele="desktop";
    if(platform.IOS)this.modele="ios";
    if(platform.ANDROID)this.modele="android";
    this.isHandset$=breakpointObserver.observe(Breakpoints.Handset+Breakpoints.Tablet+Breakpoints.Small).pipe(map((result:any) => result.matches), shareReplay());
    this.smallScreen=breakpointObserver.observe(Breakpoints.TabletPortrait+Breakpoints.Small+Breakpoints.Medium+Breakpoints.HandsetPortrait).pipe(map((result:any) => result.matches), shareReplay());
  }

  setTitle(newTitle:string){
    this.titleService.setTitle(newTitle);
  }

  setFavicon(favicon_path:string="") {
    for (let f of ["favicon", "apple_favicon"]) {
      let favIcon: HTMLLinkElement | null = document.querySelector('#' + f);
      if (favIcon) favIcon.href = favicon_path == '' ? favicon_path : `favicon.png`;
    }
  }



  resize(w:number) {
    this.width=w;
    this.large=w>500;
  }
}
