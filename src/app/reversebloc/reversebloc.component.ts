import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-reversebloc',
  templateUrl: './reversebloc.component.html',
  styleUrls: ['./reversebloc.component.scss']
})
export class ReverseblocComponent implements OnInit {

  @Input() image="";
  @Input() width="300px";
  @Input() minwidth="350px";
  @Input() maxwidth="450px";
  @Input() height="300px";
  @Input() reverse=false;

  constructor() { }

  ngOnInit(): void {
  }

}
