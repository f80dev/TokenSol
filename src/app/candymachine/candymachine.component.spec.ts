import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CandymachineComponent } from './candymachine.component';
import {ActivatedRoute, Router} from "@angular/router";
import {MatSnackBar, MatSnackBarModule} from "@angular/material/snack-bar";
import {Location} from "@angular/common";
import {NetworkService} from "../network.service";
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";

describe('CandymachineComponent', () => {
  let component: CandymachineComponent;
  let fixture: ComponentFixture<CandymachineComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CandymachineComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CandymachineComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
