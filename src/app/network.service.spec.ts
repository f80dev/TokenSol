import { TestBed } from '@angular/core/testing';

import { NetworkService } from './network.service';
import {HttpClientModule} from "@angular/common/http";

describe('NetworkService', () => {
  let service: NetworkService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule]
    });
    service = TestBed.inject(NetworkService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('return collection', () => {
    service.get_collections("paul").subscribe((r:any)=>{
      expect(r).toEqual([]);
    })
  });




});
