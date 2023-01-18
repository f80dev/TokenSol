import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthentComponent } from './authent.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";

import {GOOGLE_CLIENT_ID} from "../../definitions";

describe('AuthentComponent', () => {
  let component: AuthentComponent;
  let fixture: ComponentFixture<AuthentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AuthentComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule],
      providers:[
      ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
