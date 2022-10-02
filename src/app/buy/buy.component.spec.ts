import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BuyComponent } from './buy.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('BuyComponent', () => {
  let component: BuyComponent;
  let fixture: ComponentFixture<BuyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BuyComponent ],
      imports: [HttpClientModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BuyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
