import {Injectable} from '@angular/core';
import {Platform} from "@angular/cdk/platform";
import {Observable} from "rxjs";
import {BreakpointObserver, Breakpoints} from "@angular/cdk/layout";
import {map, shareReplay} from "rxjs/operators";



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
      platform:Platform
  ) {
    this.modele="desktop";
    if(platform.IOS)this.modele="ios";
    if(platform.ANDROID)this.modele="android";
    this.isHandset$=breakpointObserver.observe(Breakpoints.Handset+Breakpoints.Tablet+Breakpoints.Small).pipe(map((result:any) => result.matches), shareReplay());
    this.smallScreen=breakpointObserver.observe(Breakpoints.TabletPortrait+Breakpoints.Small+Breakpoints.Medium+Breakpoints.HandsetPortrait).pipe(map((result:any) => result.matches), shareReplay());
  }

  resize(w:number) {
    this.width=w;
    this.large=w>500;
  }
}
