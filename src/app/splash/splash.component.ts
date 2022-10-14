import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-splash',
  templateUrl: './splash.component.html',
  styleUrls: ['./splash.component.css']
})
export class SplashComponent implements OnInit {
  @Input() appname: any;
  @Input() description: any;
  @Input() image: string="forge.jpg";

  constructor() { }

  ngOnInit(): void {
  }

}
