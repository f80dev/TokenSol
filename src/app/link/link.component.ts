import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-link',
  templateUrl: './link.component.html',
  styleUrls: ['./link.component.css']
})
export class LinkComponent implements OnInit {

  @Input() content="";
  @Input() icon="";
  @Input() network="elrond-devnet";

  constructor() { }

  ngOnInit(): void {
  }

  get_explorer(content: string) {
    return "https://"+(this.network.indexOf('devnet')>-1 ? "devnet-" : "")+"explorer.elrond.com/address/"+content;
  }
}
