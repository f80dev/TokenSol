import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-svg',
  templateUrl: './svg.component.html',
  styleUrls: ['./svg.component.css']
})
export class SvgComponent implements OnInit {
  images: string[]=[];

  constructor(
    public network:NetworkService
  ) { }

  ngOnInit(): void {
  }

  onupload($event: any) {

  }
}
